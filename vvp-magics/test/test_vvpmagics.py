import unittest

import requests_mock

from vvpmagics import VvpMagics
from vvpmagics.vvpsession import VvpSession


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

    def test_flink_sql_executes_show_tables(self,requests_mock):

        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        sql_magic_line = ""
        sql_magic_cell = "SHOW TABLES"

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'RESULT_SUCCESS_WITH_ROWS'
