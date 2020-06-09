import json

from IPython.core.magic import (Magics, magics_class, line_magic)
import requests
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):
    vvpBaseUrl = ""
    namespacesEndpoint = "/namespaces/v1/namespaces"

    @line_magic
    @magic_arguments()
    @argument('hostname', type=str, help='Hostname')
    @argument('-p', '--port', type=str, default="8080", help='Port')
    @argument('-n', '--namespace', type=str, help='Namespace. If empty, lists all namespaces.')
    def connect_vvp(self, hostname):
        args = parse_argstring(self.connect_vvp, hostname)
        hostname = args.hostname
        port = args.port
        self.vvpBaseUrl = "http://{}:{}".format(hostname, port)

        if args.namespace:
            return self._get_namespace(args.namespace)
        else:
            return self._get_namespaces()

    def _get_namespaces(self):
        url = self.vvpBaseUrl + self.namespacesEndpoint
        return self._get_NamespaceResponse(url)

    def _get_namespace(self, namespace):
        url = self.vvpBaseUrl + self.namespacesEndpoint + "/{}".format(namespace)
        return self._get_NamespaceResponse(url)

    @staticmethod
    def _get_NamespaceResponse(url):
        print("Requesting from {}...".format(url))
        request = requests.get(url)
        namespaces = json.loads(request.text)
        return namespaces
