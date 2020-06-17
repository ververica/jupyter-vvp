import os
import string
import unittest
import random

import requests_mock

from vvpmagics import VvpMagics
from vvpmagics.flinksql import SqlSyntaxException, FlinkSqlRequestException
from vvpmagics.vvpsession import VvpSession

# if VVP_LOCAL_RUNNING has any value (even false/0) then all tests will run
has_running_vvp_instance = os.environ.get('VVP_LOCAL_RUNNING', False)


def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


def random_string():
    return ''.join(random.choices(string.digits + "abcdef", k=4))


@requests_mock.Mocker(real_http=True)
class VvpMagicsTests(unittest.TestCase):

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def test_connect_vvp_calls_namespaces_endpoint_if_none_given(self, requests_mock):
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces',
                              text="""
        { "namespaces": [{ "name": "namespaces/default" }] }
        """)

        magic_line = "localhost -p 8080"
        magics = VvpMagics()

        response = magics.connect_vvp(magic_line)

        assert not len(response['namespaces']) == 0

    def test_connect_vvp_creates_session_if_namespace_given(self, requests_mock):
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces/default',
                              text="""
        { "namespace": [{ "name": "namespaces/default" }] }
        """)
        magic_line = "localhost -n default -s session1"
        magics = VvpMagics()

        session = magics.connect_vvp(magic_line)

        assert session.get_namespace() is not None

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_show_tables(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        sql_magic_line = ""
        sql_magic_cell = "SHOW TABLES"

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'RESULT_SUCCESS_WITH_ROWS'

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_create_table(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        table_name = "testTable{}".format(random_string())

        sql_magic_line = ""
        sql_magic_cell = """CREATE TABLE `{}` (id int)
COMMENT 'SomeComment'
WITH (
'connector.type' = 'kafka',
'connector.version' = 'universal',
'connector.topic' = 'testTopic',
'connector.properties.bootstrap.servers' = 'localhost',
'connector.properties.group.id' = 'testGroup',
'connector.startup-mode' = 'earliest-offset'
)""".format(table_name)

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'RESULT_SUCCESS'

    def test_flink_sql_executes_valid_command_statement(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_validate_endpoint("default")),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_COMMAND_STATEMENT" } """)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_execute_endpoint("default")),
                              text=""" { "result": "A_GOOD_RESULT" } """)

        sql_magic_line = ""
        sql_magic_cell = """FAKE SQL COMMAND"""

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'A_GOOD_RESULT'

    def test_flink_sql_executes_valid_ddl_statement(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_validate_endpoint("default")),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_DDL_STATEMENT" } """)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_execute_endpoint("default")),
                              text=""" { "result": "CREATED_SOMETHING" } """)

        sql_magic_line = ""
        sql_magic_cell = """FAKE SQL COMMAND"""

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'CREATED_SOMETHING'

    def test_flink_sql_throws_if_statement_bad(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_validate_endpoint("default")),
                              text=""" { "validationResult": "VALIDATION_RESULT_INVALID" } """)

        sql_magic_line = ""
        sql_magic_cell = """BAD SQL COMMAND"""

        expected_exception = magics.flink_sql(sql_magic_line, sql_magic_cell)

        assert expected_exception.sql == sql_magic_cell

    def test_flink_sql_throws_if_response_unsupported(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_validate_endpoint("default")),
                              text=""" { "validationResult": "SOME_UNSUPPORTED_RESPONSE" } """)

        sql_magic_line = ""
        sql_magic_cell = """SOME SQL COMMAND"""

        with self.assertRaises(FlinkSqlRequestException) as raised_exception:
            magics.flink_sql(sql_magic_line, sql_magic_cell)

        assert raised_exception.exception.sql == sql_magic_cell

    def test_flink_sql_throws_if_validation_status_not_200(self, requests_mock):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        requests_mock.request(method='post', url='http://localhost:8080{}'.format(sql_validate_endpoint("default")),
                              text=""" { "validationResult": "VALIDATION_RESULT_INVALID" } """,
                              status_code=400)

        sql_magic_line = ""
        sql_magic_cell = """SOME SQL COMMAND"""

        with self.assertRaises(FlinkSqlRequestException) as raised_exception:
            magics.flink_sql(sql_magic_line, sql_magic_cell)

        assert raised_exception.exception.sql == sql_magic_cell
