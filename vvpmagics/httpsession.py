import requests
from requests import auth


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpSession:

    def __init__(self, base_url, headers, api_key=None, allow_self_signed_cert=False):
        self._base_url = base_url
        self._headers = headers
        self._auth = ApiKeyAuth(api_key) if api_key else None
        self._session = requests.Session()
        if allow_self_signed_cert:
            self._session.verify = False

    def get_base_url(self):
        return self._base_url

    def get(self, path, request_headers=None):
        return self._send_request(path, 'get', request_headers)

    def delete(self, path, request_headers=None):
        return self._send_request(path, 'delete', request_headers)

    def post(self, path, data, request_headers=None):
        return self._send_request(path, 'post', request_headers, data)

    def patch(self, path, data, request_headers=None):
        return self._send_request(path, 'patch', request_headers, data)

    def _send_request(self, path, method, request_headers, data=None):
        url = self._base_url + path
        headers = {**(self._headers or {}), **(request_headers or {})}
        return self._session.request(method, url, auth=self._auth, headers=headers, data=data)


class ApiKeyAuth(auth.AuthBase):

    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, request):
        request.headers['Authorization'] = "Bearer " + self.api_key
        return request
