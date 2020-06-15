import json

from .httpsession import HttpSession


class VvpSession:
    _namespace = ""
    namespacesEndpoint = "/namespaces/v1/namespaces"

    def __init__(self, vvpbaseurl: str, namespace: str):
        """

        :type namespace: string
        :type vvpbaseurl: string
        """

        self._http_session = HttpSession(vvpbaseurl, None)
        if not self._is_valid_namespace(namespace):
            raise Exception("Invalid or empty namespace specified.")
        self._namespace = namespace

    def get_namespace(self):
        return self._namespace

    def get_namespace_info(self):
        return self._get_namespace(self._namespace)

    def _is_valid_namespace(self, namespace):
        if not namespace:
            return False

        request = self._http_session.get(self.namespacesEndpoint + "/{}".format(namespace))
        validity_from_statuscodes = {200: True, 404: False}
        return validity_from_statuscodes[request.status_code]

    def _get_namespace(self, namespace):
        request = self._http_session.get(self.namespacesEndpoint + "/{}".format(namespace))
        namespace = (json.loads(request.text))["namespace"]
        return namespace

    def submit_post_request(self, endpoint, requestbody):
        request = self._http_session.post(
            path=endpoint,
            request_headers={"Content-Type": "text/plain"},
            data=requestbody
        )
        return request
