from IPython.core.magic import (Magics, magics_class, line_magic)
import requests

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):
    vvpBaseUrl = ""
    namespacesEndpoint = "/namespaces/v1/namespaces"

    @line_magic
    def connect_vvp(self, line, hostname, port, namespace):
        self.vvpBaseUrl = "https://{}:{}".format(hostname, port)
        if not (hostname & port):
            raise Exception("A hostname and port were not specified.")
        if not namespace:
            return self._get_namespaces()
        return self._get_namespace(namespace)

    def _get_namespaces(self):
        url = self.vvpBaseUrl.append(self.namespacesEndpoint)
        request = requests.get(url)
        return request.text

    def _get_namespace(self, namespace):
        url = self.vvpBaseUrl.append(self.namespacesEndpoint).append("/{}".format(namespace))
        request = requests.get(url)
        return request.text
