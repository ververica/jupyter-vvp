import json
import requests
from IPython.core.magic import (Magics, magics_class, line_magic)
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

from vvpmagics.vvpsession import VvpSession

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):
    namespacesEndpoint = VvpSession.namespacesEndpoint

    @line_magic
    @magic_arguments()
    @argument('hostname', type=str, help='Hostname')
    @argument('-p', '--port', type=str, default="8080", help='Port')
    @argument('-n', '--namespace', type=str, help='Namespace. If empty, lists all namespaces.')
    def connect_vvp(self, line):
        args = parse_argstring(self.connect_vvp, line)
        hostname = args.hostname
        port = args.port
        vvp_base_url = "http://{}:{}".format(hostname, port)

        if args.namespace:
            return VvpSession(vvp_base_url, args.namespace)
        else:
            return self._get_namespaces(vvp_base_url)

    def _get_namespaces(self, url):
        url = url + self.namespacesEndpoint
        print("Requesting from {}...".format(url))
        request = requests.get(url)
        namespaces = json.loads(request.text)
        return namespaces

