import unittest
import requests_mock

from vvpmagics.vvpsession import VvpSession


@requests_mock.Mocker()
class VvpSessionTests(unittest.TestCase):
    vvpbaseurl = "http://localhost:8080"
    namespace = "test"

    def test_get_namespace_returns_namespace(self, requests_mocker):

        requests_mocker.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces', text="""
                           { "namespaces": [{ "name": "namespaces/test" }] } 
        """)
        requests_mocker.request(method='get',
                                url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace), text="""
                           { "namespace": { "name": "namespaces/test" } }
        """)

        session = VvpSession(self.vvpbaseurl, self.namespace)

        assert session.get_namespace() == self.namespace

    def test_get_namespace_info_returns_namespace(self, requests_mocker):
        requests_mocker.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces', text="""
                           { "namespaces": [{ "name": "namespaces/test" }] } 
        """)
        requests_mocker.request(method='get',
                                url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace), text="""
                           { "namespace": { "name": "namespaces/test" } }
        """)

        session = VvpSession(self.vvpbaseurl, self.namespace)

        assert session.get_namespace_info()['name'] == "namespaces/{}".format(self.namespace)
