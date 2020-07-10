import unittest
from unittest.mock import MagicMock

import requests_mock

from test.testmocks import ShellMock, ArgsMock
from vvpmagics.deploymentoutput import DeploymentOutput
from vvpmagics.deployments import NO_DEFAULT_DEPLOYMENT_MESSAGE, VvpConfigurationException, Deployments, \
    VvpParameterException, VVP_DEFAULT_PARAMETERS_VARIABLE, DeploymentException
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

    @classmethod
    def setUpClass(cls):
        cls.show_output = DeploymentOutput.show_output

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None
        DeploymentOutput.show_output = MagicMock()

    @classmethod
    def tearDownClass(cls):
        DeploymentOutput.show_output = cls.show_output

    def _setUpSession(self, requests_mock):
        requests_mock.request(method='get', url='http://localhost:8080/api/v1/namespaces/{}/deployment-targets'
                              .format(self.namespace), text="Ignored in session setup.")

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
                                 """ % deployment_id),
                              status_code=201)

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

        response = Deployments().make_deployment(cell, self.session, ShellMock({}), ArgsMock(None))
        assert response == deployment_id

    def test_make_deployment_throws_if_no_default_deployment(self, requests_mock):
        self._setUpSession(requests_mock)

        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_validate_endpoint(self.namespace)),
                              text=""" { "validationResult": "VALIDATION_RESULT_VALID_INSERT_QUERY" } """,
                              status_code=201)

        requests_mock.request(method='get',
                              url='http://localhost:8080{}'.format(deployment_defaults_endpoint(self.namespace)),
                              text="""{ "kind": "DeploymentDefaults", "spec": {} }""",
                              status_code=200
                              )

        cell = """SOME VALID DML QUERY"""

        with self.assertRaises(VvpConfigurationException) as raised_exception:
            Deployments().make_deployment(cell, self.session, ShellMock({}), ArgsMock(None))

        assert raised_exception.exception.__str__() == NO_DEFAULT_DEPLOYMENT_MESSAGE

    def test_make_deployment_throws_if_not_201_response(self, requests_mock):
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
                                 """ % deployment_id),
                              status_code=500)

        requests_mock.request(method='get',
                              url='http://localhost:8080{}'.format(deployment_defaults_endpoint(self.namespace)),
                              text=""" { "kind": "DeploymentDefaults",
                                "spec": { "deploymentTargetId": "0b7e8f13-6943-404e-9809-c14db57d195e" } } """,
                              status_code=200
                              )

        requests_mock.request(method='get',
                              url='http://localhost:8080{}/{}'.format(
                                  sql_deployment_create_endpoint(self.namespace),
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

        with self.assertRaises(DeploymentException):
            Deployments().make_deployment(cell, self.session, ShellMock({}), ArgsMock(None))

    def test_set_values_from_flat_parameters(self, requests_mock):
        dictionary = {
            "initialkey1": "initialvalue1",
            "initialkey2": {
                "initialsubkey1": "initialsubvalue1",
                "initialsubkey2": "initialsubvalue2"
            }
        }
        parameters = {
            "key1.subkey1": "value1",
            "key1.subkey2": "value2",
            "initialkey1": "newvalue1",
            "initialkey2.initialsubkey2": "newsubvalue2",
            "metadata.annotations.should.be.ignored": "shouldbeignored"
        }
        expected_dictionary = {
            "key1": {
                "subkey1": "value1",
                "subkey2": "value2"
            },
            "initialkey1": "newvalue1",
            "initialkey2": {
                "initialsubkey1": "initialsubvalue1",
                "initialsubkey2": "newsubvalue2"
            }}

        Deployments.set_values_from_flat_parameters(dictionary, parameters)
        self.assertEqual(dictionary, expected_dictionary)

    def test_get_deployment_parameters_returns_default_if_none_given(self, requests_mock):
        args = ArgsMock(None)
        shell = ShellMock({VVP_DEFAULT_PARAMETERS_VARIABLE: {
            "key": "value"
        }})

        parameters = Deployments.get_deployment_parameters(shell, args)
        assert parameters == {"key": "value"}

    def test_get_deployment_parameters_returns_correct_even_if_default_set(self, requests_mock):
        args = ArgsMock(parameters="myparams")
        shell = ShellMock({
            VVP_DEFAULT_PARAMETERS_VARIABLE: {
                "key": "value"
            },
            "myparams": {
                "mykey": "myvalue"
            }
        })

        parameters = Deployments.get_deployment_parameters(shell, args)
        assert parameters == {"mykey": "myvalue"}

    def test_set_values_from_flat_parameters_throws_if_flattened_parameters_bad(self, requests_mock):
        dictionary = {}
        parameters = {
            "key": "value",
            "key.subkey": "subvalue"
        }

        with self.assertRaises(VvpParameterException):
            Deployments.set_values_from_flat_parameters(dictionary, parameters)

    def test_set_special_case_parameters_sets_correct_parameters(self, requests_mock):
        dictionary = {"key": "value",
                      "spec": {
                          "dummykey": "dummyvalue"
                      }}
        parameters = {
            "metadata.annotations.setting1": "settingvalue1",
            "metadata.annotations.setting2": "settingvalue2",
            "spec.template.metadata.annotations.my.annotation": "myvalue",
            "spec.template.spec.flinkConfiguration.flink.setting": "settingvalue",
            "ignored.parameter": "ignoredvalue"
        }
        expected_dictionary = {
            "key": "value",
            "metadata": {
                "annotations": {
                    "setting1": "settingvalue1",
                    "setting2": "settingvalue2"
                }
            },
            "spec": {
                "dummykey": "dummyvalue",
                "template": {
                    "metadata": {
                        "annotations": {
                            "my.annotation": "myvalue"
                        }
                    },
                    "spec": {
                        "flinkConfiguration": {
                            "flink.setting": "settingvalue"
                        }
                    }
                }
            }
        }
        Deployments.set_all_special_case_parameters(dictionary, parameters)
        assert dictionary == expected_dictionary
