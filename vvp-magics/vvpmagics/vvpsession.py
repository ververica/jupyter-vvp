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
            raise Exception("Invalid or empty namespace specified.")
        self.namespace = namespace
        print("Constructed vvp connection to {} with namespace {}."
              .format(self.vvpBaseUrl,self.namespace))

    def get_namespaceinfo(self):
        print("Getting information for namespace {}."
              .format(self.namespace))
        return self._get_namespace(self.namespace)

    def _is_valid_namespace(self, namespace):
        if not namespace:
            return False

        url = self.vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        request = requests.get(url)
        validity_from_statuscodes = {200: True, 404: False}
        return validity_from_statuscodes[request.status_code]

    def _get_namespace(self,namespace):
        url = self.vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        request = requests.get(url)
        namespace = (json.loads(request.text))["namespace"]
        return namespace
