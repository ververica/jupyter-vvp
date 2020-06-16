import unittest
import requests_mock

from vvpmagics.httpsession import HttpSession


@requests_mock.Mocker()
class HttpSessionTests(unittest.TestCase):
    baseurl = "http://localhost:8080"
    path = "/test"
    return_text = "Hello, world."

    def test_get_request(self, requests_mocker):

        requests_mocker.request(
            method='get', url='http://localhost:8080{}'.format(self.path), text=self.return_text)

        result = HttpSession(self.baseurl, None).get(self.path)

        assert result.status_code == 200
        assert result.text == self.return_text

    def test_post_request(self, requests_mocker):
        def match_request_text(request):
            return 'test' in (request.text or '')

        requests_mocker.request(method='post', url='http://localhost:8080{}'.format(
            self.path), additional_matcher=match_request_text, text=self.return_text)

        result = HttpSession(self.baseurl, None).post(self.path, "hello world test")

        assert result.status_code == 200
        assert result.text == self.return_text

