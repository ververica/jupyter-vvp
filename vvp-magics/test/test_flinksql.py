import unittest
from unittest.mock import patch

import requests_mock

from vvpmagics import flinksql
from vvpmagics.deployments import Deployments
from vvpmagics.flinksql import run_query, SqlSyntaxException, FlinkSqlRequestException
from vvpmagics.vvpsession import VvpSession


def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


def deployment_defaults_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-defaults".format(namespace)


def sql_deployment_endpoint(namespace, deployment_id):
    return "/api/v1/namespaces/{}/deployments/{}".format(namespace, deployment_id)


def sql_deployment_create_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployments".format(namespace)


@requests_mock.Mocker()
class FlinkSqlTests(unittest.TestCase):
    vvp_base_url = "http://localhost:8080"
    namespace = "test"

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def _setUpSession(self, requests_mock):
        namespaces_response = " {{ 'namespaces': [{{ 'name': 'namespaces/{}' }}] }}".format(self.namespace)
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces',
                              text=namespaces_response)

        requests_mock.request(method='get',
                              url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace),
                              text="""
                                {{ "namespace": [{{ "name": "namespaces/{}" }}] }}
                                """.format(self.namespace))
        self.session = VvpSession.create_session(self.vvp_base_url, self.namespace, "session1")

    def test_run_query_returns_command_response_for_valid_command(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_COMMAND_STATEMENT" } """)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_execute_endpoint(self.namespace)),
                              text=""" {"result": "RESULT_SUCCESS_WITH_ROWS",
                                 "resultTable": {"headers": [{"name": "table name"}],
                                  "rows": [{"cells": [{"value": "testTable"}]}]}} """)

        cell = """FAKE SQL COMMAND"""

        response = run_query(self.session, cell, None, None)
        assert response.iloc[0]['table name'] == 'testTable'

    def test_flink_sql_executes_valid_ddl_statement(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_DDL_STATEMENT" } """)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_execute_endpoint(self.namespace)),
                              text=""" {"result": "RESULT_SUCCESS_WITH_ROWS",
                                     "resultTable": {"headers": [{"name": "table name"}],
                                      "rows": [{"cells": [{"value": "testTable"}]}]}} """)

        cell = """FAKE SQL COMMAND"""

        response = run_query(self.session, cell, None, None)
        assert response.iloc[0]['table name'] == 'testTable'

    def test_flink_sql_executes_valid_dml_statement_with_default_parameters(self, requests_mock, ):
        self._setUpSession(requests_mock)

        args = ArgsMock(None)
        shell = ShellMock({"vvp_default_parameters": {
            "key": "value"
        }})
        deployment_id = """58ea758d-02e2-4b8e-8d60-3c36c3413bf3"""

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_INSERT_QUERY" } """)

        cell = """SOME VALID DML QUERY"""

        with patch.object(Deployments, 'make_deployment', return_value=deployment_id) as mock_make_deployment:
            response = run_query(self.session, cell, shell, args)
        assert response == deployment_id
        mock_make_deployment.assert_called_once_with(cell, self.session, shell.user_ns['vvp_default_parameters'])

    def test_flink_sql_executes_valid_dml_statement_with_specified_parameters(self, requests_mock):
        self._setUpSession(requests_mock)

        args = ArgsMock("myparamsvar")
        shell = ShellMock({"myparamsvar": {
            "key": "value"
        }})
        deployment_id = """58ea758d-02e2-4b8e-8d60-3c36c3413bf3"""

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_INSERT_QUERY" } """)

        cell = """SOME VALID DML QUERY"""

        with patch.object(Deployments, 'make_deployment', return_value=deployment_id) as mock_make_deployment:
            response = run_query(self.session, cell, shell, args)
        assert response == deployment_id
        mock_make_deployment.assert_called_once_with(cell, self.session, shell.user_ns['myparamsvar'])

    def test_flink_sql_throws_if_statement_bad(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text="""{"validationResult": "VALIDATION_RESULT_INVALID_QUERY", "errorDetails": {
                              "lineNumber": 0, "columnNumber": 0, "endLineNumber": 0, "endColumnNumber": 0, 
                              "message": "Table `default`.`default`.`test` already exists.", "cause": ""}} """)

        cell = """BAD SQL COMMAND"""

        with self.assertRaises(SqlSyntaxException) as raised:
            run_query(self.session, cell, None, None)
            assert raised.exception.sql == cell

    def test_flink_sql_throws_if_response_unsupported(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "SOME_UNSUPPORTED_RESPONSE" } """)

        cell = """SOME SQL COMMAND"""

        with self.assertRaises(FlinkSqlRequestException) as raised_exception:
            run_query(self.session, cell, None, None)

        assert raised_exception.exception.sql == cell

    def test_flink_sql_throws_if_validation_status_not_200(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_INVALID" } """,
                              status_code=400)

        cell = """SOME SQL COMMAND"""

        with self.assertRaises(FlinkSqlRequestException) as raised_exception:
            run_query(self.session, cell, None, None)
            assert raised_exception.exception.sql == cell


class ArgsMock:
    def __init__(self, parameters):
        self.parameters = parameters


class ShellMock:
    def __init__(self, user_ns):
        self.user_ns = user_ns


if __name__ == '__main__':
    unittest.main()
