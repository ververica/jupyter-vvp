import json
import requests
from IPython import get_ipython
from IPython.core.magic import (Magics, magics_class, line_magic)
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

from vvpmagics.vvpsession import VvpSession

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):
    vvpBaseUrl = ""
    namespacesEndpoint = VvpSession.namespacesEndpoint

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
            return VvpSession(self.vvpBaseUrl, args.namespace)
        else:
            return self._get_namespaces(self.vvpBaseUrl)

    def _get_namespaces(self, url):
        url = url + self.namespacesEndpoint
        print("Requesting from {}...".format(url))
        request = requests.get(url)
        namespaces = json.loads(request.text)
        return namespaces

