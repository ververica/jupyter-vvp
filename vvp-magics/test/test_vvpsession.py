import unittest
import requests_mock

from vvpmagics.vvpsession import VvpSession


@requests_mock.Mocker()
class VvpSessionTests(unittest.TestCase):
    vvp_base_url = "http://localhost:8080"
    namespace = "test"

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def test_get_namespace_returns_namespace(self, requests_mocker):
        requests_mocker.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces', text="""
                           { "namespaces": [{ "name": "namespaces/test" }] } 
        """)
        requests_mocker.request(method='get',
                                url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace), text="""
                           { "namespace": { "name": "namespaces/test" } }
        """)

        session = VvpSession(self.vvp_base_url, self.namespace)

        assert session.get_namespace() == self.namespace

    def test_get_namespace_info_returns_namespace(self, requests_mocker):
        requests_mocker.request(method='get', url='http://localhost:8080/namespaces/v1/namespaces', text="""
                           { "namespaces": [{ "name": "namespaces/test" }] } 
        """)
        requests_mocker.request(method='get',
                                url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace), text="""
                           { "namespace": { "name": "namespaces/test" } }
        """)

        session = VvpSession(self.vvp_base_url, self.namespace)

        assert session.get_namespace_info()['name'] == "namespaces/{}".format(self.namespace)

    def test_create_session(self, requests_mocker):
        requests_mocker.request(method='get',
                                url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace), text="""
                           { "namespace": { "name": "namespaces/test" } }
        """)

        first_session = VvpSession.create_session(self.vvp_base_url, self.namespace, "session1", set_default=True)
        assert first_session.get_namespace() == self.namespace
        assert VvpSession._sessions['session1'] == first_session
        assert VvpSession.default_session_name == "session1"

        second_session = VvpSession.create_session(self.vvp_base_url, self.namespace, "session2", set_default=False)
        assert VvpSession._sessions['session2'] == second_session
        assert VvpSession.default_session_name == "session1"

    def test_get_sessions(self, requests_mocker):
        requests_mocker.request(method='get',
                                url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace), text="""
                           { "namespace": { "name": "namespaces/test" } }
        """)

        VvpSession.create_session(self.vvp_base_url, self.namespace, "session1", set_default=True)
        sessions = VvpSession.get_sessions()

        assert "session1" in sessions


if __name__ == '__main__':
    unittest.main()
