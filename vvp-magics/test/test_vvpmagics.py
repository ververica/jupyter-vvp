import unittest

import requests_mock

from vvpmagics import VvpMagics
from vvpmagics.vvpsession import VvpSession


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


if __name__ == '__main__':
    unittest.main()
