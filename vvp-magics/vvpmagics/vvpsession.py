import json

import requests


class VvpSession:
    vvpBaseUrl = ""
    namespace = ""
    namespacesEndpoint = "/namespaces/v1/namespaces"

    def __init__(self, vvpbaseurl: str, namespace: str):
        """

        :type namespace: string
        :type vvpbaseurl: string
        """

        self.vvpBaseUrl = vvpbaseurl
        if not namespace:
            raise Exception("Trying to build a session with an empty namespace.")
        if not self._is_valid_namespace(namespace):
            raise Exception("Invalid namespace specified.")
        self.namespace = namespace

    def test_connection(self):
        return self._get_namespace(self.namespace)

    def _is_valid_namespace(self, namespace):
        url = self.vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        print("Requesting namespaces from {}...".format(url))
        request = requests.get(url)
        validity_from_statuscodes = {200: True, 404: False}
        return validity_from_statuscodes[request.status_code]

    def _get_namespace(self,namespace):
        url = self.vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        request = requests.get(url)
        namespace = (json.loads(request.text))["namespace"]
        return namespace
