from IPython.core.magic import magics_class, Magics, cell_magic
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

from vvpmagics.vvpsession import VvpSession


@magics_class
class VvpDdlMagics(Magics):
    namespaces_endpoint = VvpSession.namespacesEndpoint

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
