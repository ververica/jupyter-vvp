import os
import string
import unittest
import random

import requests_mock

from vvpmagics import VvpMagics
from vvpmagics.vvpsession import VvpSession

# if VVP_LOCAL_RUNNING has any value (even false/0) then all tests will run
has_running_vvp_instance = os.environ.get('VVP_LOCAL_RUNNING', False)


def random_string():
    return ''.join(random.choices(string.digits + "abcdef", k=4))


@requests_mock.Mocker()
class VvpMagicsTests(unittest.TestCase):
    namespace = "default"

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def setUpMocks(self, requests_mock):
        namespaces_response = " {{ 'namespaces': [{{ 'name': 'namespaces/{}' }}] }}".format(self.namespace)
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces',
                              text=namespaces_response)

        requests_mock.request(method='get',
                              url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace),
                              text="""
        {{ "namespace": [{{ "name": "namespaces/{}" }}] }}
        """.format(self.namespace))

    def test_connect_vvp_calls_namespaces_endpoint_if_none_given(self, requests_mock):
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces',
                              text="""
        { "namespaces": [{ "name": "namespaces/default" }] }
        """)

        magic_line = "localhost -p 8080"
        magics = VvpMagics()

        response = magics.connect_vvp(magic_line)

        assert response['namespaces']

    def test_connect_vvp_creates_session_if_namespace_given(self, requests_mock):
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces/default',
                              text="""
        { "namespace": [{ "name": "namespaces/default" }] }
        """)
        magic_line = "localhost -n default -s session1"
        magics = VvpMagics()

        session = magics.connect_vvp(magic_line)

        assert session.get_namespace() is not None


class VvpMagicsTestsAgainstBackend(unittest.TestCase):

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_show_tables(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        sql_magic_line = ""
        sql_magic_cell = "SHOW TABLES"

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'RESULT_SUCCESS_WITH_ROWS'

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_create_table(self):
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


if __name__ == '__main__':
    unittest.main()
