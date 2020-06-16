import requests


class HttpSession:

    def __init__(self, base_url, headers):
        self._base_url = base_url
        self._headers = headers

        self._session = requests.Session()

    def get(self, path, request_headers=None):
        return self._send_request(path, 'get', request_headers)

    def post(self, path, data, request_headers=None):
        return self._send_request(path, 'post', request_headers, data)

    def _send_request(self, path, method, request_headers, data=None):
        url = self._base_url + path
        headers = {**(self._headers or {}), **(request_headers or {})}
        response = self._session.request(method, url, headers=headers, data=data)

        return response
