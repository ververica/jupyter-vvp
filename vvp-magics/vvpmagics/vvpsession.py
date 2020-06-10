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
        if not self._is_valid_namespace(namespace):
            raise Exception("Invalid namespace specified.")
        self.namespace = namespace

    def test_connection(self):
        return self._is_valid_namespace(self.namespace)

    def _is_valid_namespace(self, namespace):
        url = self.vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        self._get_namespace(url)
        return True

    @staticmethod
    def _get_namespace(url):
        print("Requesting namespaces from {}...".format(url))
        request = requests.get(url)
        namespace = (json.loads(request.text))["namespace"]
        return namespace
