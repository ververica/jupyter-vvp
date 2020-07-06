import unittest
from unittest.mock import MagicMock

import requests_mock

from vvpmagics import VvpMagics
from vvpmagics.vvpsession import VvpSession


@requests_mock.Mocker()
class VvpMagicsTests(unittest.TestCase):
    namespace = "test"

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def setUpMocks(self, requests_mock):
        namespaces_response = '{{ "namespaces": [{{ "name": "namespaces/{}" }}] }}'.format(self.namespace)
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces',
                              text=namespaces_response)

        requests_mock.request(method='get',
                              url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace),
                              text="""
        {{ "namespace": [{{ "name": "namespaces/{}" }}] }}
        """.format(self.namespace))
        requests_mock.request(method='get', url='http://localhost:8080/api/v1/namespaces/{}/deployment-targets'
                              .format(self.namespace), text="Ignored in session setup.")

    def setup_mocks_with_key(self, requests_mock, key):
        def match_headers(request):
            return request.headers['Authorization'] == "Bearer {}".format(key)

        requests_mock.request(method='get', url='http://localhost:8080/api/v1/namespaces/{}/deployment-targets'
                              .format(self.namespace), additional_matcher=match_headers,
                              text="Ignored in session setup.")
        requests_mock.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces',
                              additional_matcher=match_headers,
                              text="""
        { "namespaces": [{ "name": "namespaces/test" }] }
        """)

    def test_connect_vvp_calls_namespaces_endpoint_if_none_given(self, requests_mock):
        self.setUpMocks(requests_mock)
        magic_line = "localhost -p 8080"
        magics = VvpMagics()

        response = magics.connect_vvp(magic_line)

        assert response['namespaces']

    def test_connect_vvp_creates_session_if_namespace_given(self, requests_mock):
        self.setUpMocks(requests_mock)

        magic_line = "localhost -n {} -s session1".format(self.namespace)
        magics = VvpMagics()

        session = magics.connect_vvp(magic_line)

        assert session.get_namespace() is not None

    def test_connect_vvp_uses_api_key(self, requests_mock):
        key = "myApiKey"
        self.setup_mocks_with_key(requests_mock, key)

        magic_line_with_session = "localhost -n {} -s session1 -k {}".format(self.namespace, key)
        magic_line_without_session = "localhost -k {}".format(key)
        magics = VvpMagics()

        session = magics.connect_vvp(magic_line_with_session)
        assert session._http_session._auth.api_key == key

        namespaces = magics.connect_vvp(magic_line_without_session)
        assert namespaces["namespaces"][0]["name"] == "namespaces/test"

    def test_connect_vvp_with_session_requests_api_key(self, requests_mock):
        key = "myApiKey"
        self.setup_mocks_with_key(requests_mock, key)

        magic_line_with_session = "localhost -n {} -s session1 -K".format(self.namespace)
        magics = VvpMagics()

        VvpMagics.get_api_key_interactively = MagicMock(return_value=key)
        session = magics.connect_vvp(magic_line_with_session)
        assert session._http_session._auth.api_key == key
        VvpMagics.get_api_key_interactively.assert_called_once()

    def test_connect_vvp_without_session_requests_api_key(self, requests_mock):
        key = "myApiKey"
        self.setup_mocks_with_key(requests_mock, key)

        magic_line_without_session = "localhost -K"
        magics = VvpMagics()

        VvpMagics.get_api_key_interactively = MagicMock(return_value=key)

        namespaces = magics.connect_vvp(magic_line_without_session)
        assert namespaces["namespaces"][0]["name"] == "namespaces/test"
        VvpMagics.get_api_key_interactively.assert_called_once()


if __name__ == '__main__':
    unittest.main()
