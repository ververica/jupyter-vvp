import unittest
import json

import requests_mock

from vvpmagics.flinksql import run_query, _json_convert_to_dataframe, SqlSyntaxException, FlinkSqlRequestException
from vvpmagics.vvpsession import VvpSession
from pandas import DataFrame


def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


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

    def test_flink_sql_throws_if_statement_bad(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_INVALID" } """)

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


class JsonTests(unittest.TestCase):
    def test_json_conversion(self):
        json_string = """{"result": "RESULT_SUCCESS_WITH_ROWS",
 "resultTable": {"headers": [{"name": "name"},
   {"name": "type"},
   {"name": "null"},
   {"name": "key"},
   {"name": "computed column"},
   {"name": "watermark"}],
  "rows": [{"cells": [{"value": "id"},
     {"value": "INT"},
     {"value": "true"},
     {"value": ""},
     {"value": ""},
     {"value": ""}]}]}}"""

        json_data = json.loads(json_string)
        df = _json_convert_to_dataframe(json_data)
        assert df.iloc[0]['name'] == 'id'
        assert df.iloc[0]['type'] == 'INT'
        assert df.iloc[0]['null'] == 'true'

    def test_json_conversion_ignores_results_without_table(self):
        json_string = """{"result": "RESULT_NO_TABLE"}"""

        json_data = json.loads(json_string)
        result = _json_convert_to_dataframe(json_data)
        print(result)
        assert result == json_data


if __name__ == '__main__':
    unittest.main()

