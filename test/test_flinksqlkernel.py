import unittest
from unittest.mock import patch

import requests_mock

from jupytervvp import flinksqlkernel
from jupytervvp.deployments import Deployments
from jupytervvp.flinksql import run_query, SqlSyntaxException, FlinkSqlRequestException
from jupytervvp.flinksqlkernel import _do_flink_completion, calculate_text_length
from jupytervvp.vvpsession import VvpSession


def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)

def sql_complete_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:suggest".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


def deployment_defaults_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-defaults".format(namespace)


def sql_deployment_endpoint(namespace, deployment_id):
    return "/api/v1/namespaces/{}/deployments/{}".format(namespace, deployment_id)


def sql_deployment_create_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployments".format(namespace)


@requests_mock.Mocker()
class FlinkSqlTests(unittest.TestCase):
    vvp_base_url = "http://localhost:8080"
    namespace = "test"

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def _setUpSession(self, requests_mock):
        requests_mock.request(method='get', url='http://localhost:8080/api/v1/namespaces/{}/deployment-targets'
                              .format(self.namespace), text="Ignored in session setup.")

        requests_mock.request(method='get',
                              url='http://localhost:8080/namespaces/v1/namespaces/{}'.format(self.namespace),
                              text="""
                                {{ "namespace": [{{ "name": "namespaces/{}" }}] }}
                                """.format(self.namespace))
        self.session = VvpSession.create_session(self.vvp_base_url, self.namespace, "session1")

    def test_complete_correct_line(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_complete_endpoint(self.namespace)),
                              text=""" {
                                          "completions": [{
                                            "text": "TABLES",
                                            "type": "HINT_TYPE_UNKNOWN"
                                          }]
                                        } """)

        cell = """%%flink_sql\nSHOW TAB"""

        response = _do_flink_completion(cell, 20)
        assert response['status'] == 'ok'
        assert response['matches'][0] == "TABLES"
        assert response['cursor_end'] == 20
        assert response['cursor_start'] == 17

    def test_ignore_cursor_in_command_line(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_complete_endpoint(self.namespace)),
                              text=""" {
                                          "completions": [{
                                            "text": "TABLES",
                                            "type": "HINT_TYPE_UNKNOWN"
                                          }]
                                        } """)

        cell = """%%flink_sql\nSHOW TAB"""

        response = _do_flink_completion(cell, 6)
        assert response is None

    def test_ignore_wrong_session(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_complete_endpoint(self.namespace)),
                              text=""" {
                                          "completions": [{
                                            "text": "TABLES",
                                            "type": "HINT_TYPE_UNKNOWN"
                                          }]
                                        } """)

        cell = """%%flink_sql -s no_such_session\nSHOW TAB"""

        response = _do_flink_completion(cell, 38)
        assert response is None

    def test_deal_with_errors(self, requests_mock):
        self._setUpSession(requests_mock)
        requests_mock.request(method='post',
                              url='http://localhost:8080{}'.format(sql_complete_endpoint(self.namespace)),
                              text=""" {
                                          "error": "Does not compute"
                                        } """)

        cell = """%%flink_sql\nSHOW TAB"""

        response = _do_flink_completion(cell, 38)
        assert response is None

    def test_text_length_calculation(self, requests_mock):
        cell = """%%flink_sql\nSHOW TAB"""
        length = calculate_text_length(cell, 20)

        print(length)
        assert length == 3

    def test_text_length_calculation_previous_word(self, requests_mock):
        cell = """%%flink_sql\nSHOW TAB"""
        length = calculate_text_length(cell, 16)

        print(length)
        assert length == 4

    def test_text_length_calculation_whiteline(self, requests_mock):
        cell = """%%flink_sql\nSHOW TAB"""
        length = calculate_text_length(cell, 17)

        print(length)
        assert length == 0

    def test_text_length_calculation_commandline(self, requests_mock):
        cell = """%%flink_sql\nSHOW TAB"""
        length = calculate_text_length(cell, 9)

        print(length)
        assert length == 9

if __name__ == '__main__':
    unittest.main()
