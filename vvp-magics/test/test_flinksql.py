import unittest

import requests_mock

from vvpmagics.flinksql import run_query, SqlSyntaxException, FlinkSqlRequestException
from vvpmagics.deployments import NO_DEFAULT_DEPLOYMENT_MESSAGE, VvpConfigurationException
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
class VvpSessionTests(unittest.TestCase):
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

        response = run_query(self.session, cell)
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

        response = run_query(self.session, cell)
        assert response.iloc[0]['table name'] == 'testTable'

    def test_flink_sql_executes_valid_dml_statement(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_INSERT_QUERY" } """)

        deployment_id = """58ea758d-02e2-4b8e-8d60-3c36c3413bf3"""
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_deployment_create_endpoint(self.namespace)),
                              text=("""{
  "kind" : "Deployment",
  "metadata" : {
    "id" : "%s",
    "name" : "INSERT INTO testTable1836f SELECT * FROM testTable22293",
    "namespace" : "default"
  },
  "spec" : {
    "state" : "RUNNING",
    "deploymentTargetId" : "0b7e8f13-6943-404e-9809-c14db57d195e"
  } 
  }
  """ % deployment_id))

        requests_mock.request(method='get',
                              url='http://localhost:8080{}'.format(deployment_defaults_endpoint(self.namespace)),
                              text=""" { "kind": "DeploymentDefaults",
                                "spec": { "deploymentTargetId": "0b7e8f13-6943-404e-9809-c14db57d195e" } } """,
                              status_code=200
                              )

        requests_mock.request(method='get',
                              url='http://localhost:8080{}/{}'.format(sql_deployment_create_endpoint(self.namespace),
                                                                      deployment_id),
                              text="""{"DummyKey": "DummyValue"}""",
                              status_code=200
                              )
        requests_mock.request(method='get',
                              url='http://localhost:8080{}'.format(
                                  sql_deployment_endpoint(self.namespace, deployment_id)),
                              text="""{ "kind" : "Deployment",   "status" : {
    "state" : "RUNNING",
    "running" : { "jobId" : "68ab92d0-1acc-459f-a6ed-26a374e08717" }
  }
 }""")

        cell = """SOME VALID DML QUERY"""

        response = run_query(self.session, cell)
        assert response == deployment_id

    def test_flink_sql_throws_if_statement_bad(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text="""{"validationResult": "VALIDATION_RESULT_INVALID_QUERY", "errorDetails": {
                              "lineNumber": 0, "columnNumber": 0, "endLineNumber": 0, "endColumnNumber": 0, 
                              "message": "Table `default`.`default`.`test` already exists.", "cause": ""}} """)

        cell = """BAD SQL COMMAND"""

        with self.assertRaises(SqlSyntaxException) as raised:
            run_query(self.session, cell)
            assert raised.exception.sql == cell

    def test_flink_sql_throws_if_response_unsupported(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "SOME_UNSUPPORTED_RESPONSE" } """)

        cell = """SOME SQL COMMAND"""

        with self.assertRaises(FlinkSqlRequestException) as raised_exception:
            run_query(self.session, cell)

        assert raised_exception.exception.sql == cell

    def test_flink_sql_throws_if_validation_status_not_200(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_INVALID" } """,
                              status_code=400)

        cell = """SOME SQL COMMAND"""

        with self.assertRaises(FlinkSqlRequestException) as raised_exception:
            run_query(self.session, cell)
            assert raised_exception.exception.sql == cell

    def test_flink_sql_throws_if_no_default_deployment(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_INSERT_QUERY" } """)

        requests_mock.request(method='get',
                              url='http://localhost:8080{}'.format(deployment_defaults_endpoint(self.namespace)),
                              text="""{ "kind": "DeploymentDefaults", "spec": {} }""",
                              status_code=200
                              )

        cell = """SOME VALID DML QUERY"""

        with self.assertRaises(VvpConfigurationException) as raised_exception:
            run_query(self.session, cell)

        assert raised_exception.exception.__str__() == NO_DEFAULT_DEPLOYMENT_MESSAGE


if __name__ == '__main__':
    unittest.main()
