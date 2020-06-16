import unittest
import requests_mock

from vvpmagics.httpsession import HttpSession


@requests_mock.Mocker()
class HttpSessionTests(unittest.TestCase):
    baseurl = "http://localhost:8080"
    path = "test"
    result = "ok"

    def test_get_request(self, requests_mocker):

        requests_mocker.request(
            method='get', url='http://localhost:8080/{}'.format(self.path), text=self.result)

        session = HttpSession(self.baseurl, None)

        assert session.get(self.path) == self.result

    def test_post_request(self, requests_mocker):
        def match_request_text(request):
            # request.text may be None, or '' prevents a TypeError.
            return 'test' in (request.text or '')

        requests_mocker.request(method='post', url='http://localhost:8080//{}'.format(
            self.path), additional_matcher=match_request_text, text=self.result)

        session = HttpSession(self.baseurl, None)

        assert session.post(self.path, "hello world test") == self.result
