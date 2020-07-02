from IPython.utils.tokenutil import line_at_cursor
from ipykernel.ipkernel import IPythonKernel

from vvpmagics.vvpsession import VvpSession, SessionException
from vvpmagics.flinksql import complete_sql
from IPython.core.magic_arguments import parse_argstring
from vvpmagics import VvpMagics
import json


def _do_flink_completion(code, cursor_pos):
    # Get VvpSession
    lines = code.split('\n')
    command = lines[0].replace('%%flink_sql', '')
    args = parse_argstring(VvpMagics.flink_sql, command)
    session_name = args.session or VvpSession.default_session_name
    if session_name is not None:
        try:
            session = VvpSession.get_session(session_name)
        except SessionException:
            session = None
    if session_name is None or session is None:
        return None

    if cursor_pos is None:
        cursor_pos = len(code)

    sql = code[(len(lines[0])+1):]
    sql_pos = cursor_pos - len(lines[0]) - 1

    # Cursor is in command line, we have special code completion there
    if sql_pos < 0:
        return None

    line, offset = line_at_cursor(code, cursor_pos)
    line_cursor = cursor_pos - offset
    text = line[:line_cursor].split()[-1]
    # print("Text: " + text + ", code: " + code, file=open('dbg.log', 'a')) # dbg

    # Request suggestions from VVP
    suggestions = complete_sql(sql, sql_pos, session)
    # print(suggestions.text, file=open('dbg.log', 'a')) # dbg

    suggest_json = json.loads(suggestions.text)
    matches = []
    for suggestion in suggest_json['completions']:
        matches.append(suggestion["text"])

    return {'matches': matches,
            'cursor_end': cursor_pos,
            'cursor_start': cursor_pos-len(text),
            'metadata': {},
            'status': 'ok'}


class FlinkSqlKernel(IPythonKernel):
    def __init__(self,**kwargs):
        super(FlinkSqlKernel, self).__init__(**kwargs)

    def do_complete(self, code, cursor_pos):
        if code.startswith('%%flink_sql'):
            completions = _do_flink_completion(code, cursor_pos)
            if completions is not None:
                return completions

        return super(FlinkSqlKernel, self).do_complete(code, cursor_pos)


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=FlinkSqlKernel)