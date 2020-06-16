import json
import requests
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic)
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

from vvpmagics import vvpsession
from vvpmagics.vvpsession import VvpSession

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):
    namespacesEndpoint = vvpsession.namespaces_endpoint

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
            return VvpSession.create_session(vvp_base_url, args.namespace)
        else:
            return self._get_namespaces(vvp_base_url)

    def _get_namespaces(self, url):
        url = url + self.namespacesEndpoint
        print("Requesting from {}...".format(url))
        request = requests.get(url)
        namespaces = json.loads(request.text)
        return namespaces

    @cell_magic
    @magic_arguments()
    @argument('session', type=str, help='Name of the object representing the connection to a given vvp namespace.')
    def execute_catalog_statement(self, line, cell):
        args = parse_argstring(self.execute_catalog_statement, line)
        session = self.shell.user_ns[args.session]
        catalog_endpoint = "/catalog/v1beta1/namespaces/{}:execute" \
            .format(session.get_namespace())
        if cell:
            response = session.submit_post_request(catalog_endpoint, cell)
            print(response)
            print(response.text)
        else:
            print("Empty cell: doing nothing.")

