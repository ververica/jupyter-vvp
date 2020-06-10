import json

import requests


class VvpSession:
    _vvpBaseUrl = ""
    _namespace = ""
    namespacesEndpoint = "/namespaces/v1/namespaces"

    def __init__(self, vvpbaseurl: str, namespace: str):
        """

        :type namespace: string
        :type vvpbaseurl: string
        """

        self._vvpBaseUrl = vvpbaseurl
        if not self._is_valid_namespace(namespace):
            raise Exception("Invalid or empty namespace specified.")
        self._namespace = namespace
        print("Constructed vvp connection to {} with namespace {}."
              .format(self._vvpBaseUrl, self._namespace))

    def get_namespace(self):
        return self._namespace

    def get_namespaceinfo(self):
        print("Getting information for namespace {}."
              .format(self._namespace))
        return self._get_namespace(self._namespace)

    def _is_valid_namespace(self, namespace):
        if not namespace:
            return False

        url = self._vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        request = requests.get(url)
        validity_from_statuscodes = {200: True, 404: False}
        return validity_from_statuscodes[request.status_code]

    def _get_namespace(self, namespace):
        url = self._vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        request = requests.get(url)
        namespace = (json.loads(request.text))["namespace"]
        return namespace

    def submit_post_request(self, endpoint, requestbody):
        url = self._vvpBaseUrl + endpoint
        request = requests.post(
            url=url,
            headers={"Content-Type": "text/plain"},
            data=requestbody
        )
        return request
