import unittest

import requests_mock

from vvpmagics.deployments import NO_DEFAULT_DEPLOYMENT_MESSAGE, VvpConfigurationException, Deployments
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
class DeploymentTests(unittest.TestCase):
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

    def test_make_deployment_returns_deployment_id(self, requests_mock):
        self._setUpSession(requests_mock)

        deployment_id = """58ea758d-02e2-4b8e-8d60-3c36c3413bf3"""
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_deployment_create_endpoint(self.namespace)),
                              text=("""{ "kind" : "Deployment",
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
                              text="""{ "kind" : "Deployment",   "status" : { "state" : "RUNNING",
                                  "running" : { "jobId" : "68ab92d0-1acc-459f-a6ed-26a374e08717" } }
                                }""")

        cell = """SOME VALID DML QUERY"""

        response = Deployments().make_deployment(cell, self.session)
        assert response == deployment_id

    def test_make_deployment_throws_if_no_default_deployment(self, requests_mock):
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
            Deployments().make_deployment(cell, self.session)

        assert raised_exception.exception.__str__() == NO_DEFAULT_DEPLOYMENT_MESSAGE
