from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic)
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring

from vvpmagics.flinksql import run_query, SqlSyntaxException
from vvpmagics.vvpsession import VvpSession

from pandas import DataFrame

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):

    @line_magic
    @magic_arguments()
    @argument('hostname', type=str, help='Hostname')
    @argument('-p', '--port', type=str, default="8080", help='Port')
    @argument('-n', '--namespace', type=str, help='Namespace. If empty, lists all namespaces.')
    @argument('-s', '--session', type=str, help='Session name')
    @argument('-f', '--force', type=bool, help='Force updating of session names.')
    def connect_vvp(self, line):
        args = parse_argstring(self.connect_vvp, line)
        hostname = args.hostname
        port = args.port
        vvp_base_url = "http://{}:{}".format(hostname, port)

        if args.namespace:
            session_name = args.session or VvpSession.default_session_name
            force_update = args.force or False
            if session_name is None:
                raise Exception("No session name given and none already exist.")
            return VvpSession.create_session(vvp_base_url, args.namespace, session_name, force=force_update)
        else:
            return VvpSession.get_namespaces(vvp_base_url)

    @cell_magic
    @magic_arguments()
    @argument('-s', '--session', type=str, help='Name of the object representing the connection '
                                                'to a given vvp namespace.')
    @argument('-o', '--output', type=str, help='Name of variable to assign the resulting data frame to. '
                                               'Nothing will be assigned if query does not result in data frame')
    def flink_sql(self, line, cell):
        args = parse_argstring(self.flink_sql, line)
        session = VvpSession.get_session(args.session)

        if cell:
            try:
                result = run_query(session, cell)
                if (args.output is not None) and (isinstance(result, DataFrame)):
                    self.shell.user_ns[args.output] = result
                return result
            except SqlSyntaxException as exception:
                print(exception.message)
                print(exception.get_details())
                raise exception
        else:
            print("Empty cell: doing nothing.")
