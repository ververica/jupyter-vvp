from IPython.utils.tokenutil import line_at_cursor
from ipykernel.ipkernel import IPythonKernel

from jupytervvp.vvpsession import VvpSession, SessionException
from jupytervvp.flinksql import complete_sql
from IPython.core.magic_arguments import parse_argstring
from jupytervvp import VvpMagics
import json


def _do_flink_completion(code, cursor_pos):
    # Get VvpSession
    lines = code.split('\n')
    command_line = lines[0]
    session = load_session(command_line)
    if session is None:
        return None

    if cursor_pos is None:
        cursor_pos = len(code)

    matches = fetch_vvp_suggestions(session, code, cursor_pos, len(command_line)+1)

    if matches is None:
        return None

    text_length = calculate_text_length(code, cursor_pos)

    return {'matches': matches,
            'cursor_end': cursor_pos,
            'cursor_start': cursor_pos - text_length,
            'metadata': {},
            'status': 'ok'}


def calculate_text_length(code, cursor_pos):
    # get length of word for completion
    line, offset = line_at_cursor(code, cursor_pos)
    line_cursor = cursor_pos - offset
    line_up_to_cursor = line[:line_cursor]
    if line_up_to_cursor.endswith(' '):
        return 0
    text = line_up_to_cursor.split()[-1]
    # print("Text: " + text + ", code: " + code, file=open('dbg.log', 'a')) # dbg
    text_length = len(text)
    return text_length


def fetch_vvp_suggestions(session, code, cursor_pos, command_line_length):
    # Strip first line to only send SQL to VVP
    sql = code[command_line_length:]
    sql_pos = cursor_pos - command_line_length

    # Cursor seems to be in the first line of the cell magic, let the normal auto completion handle that
    if sql_pos < 0:
        return None

    # Request suggestions from VVP
    suggestions = complete_sql(sql, sql_pos, session)
    # print(suggestions.text, file=open('dbg.log', 'a')) # dbg
    suggest_json = json.loads(suggestions.text)
    if 'completions' not in suggest_json:
        return None
    matches = []
    for suggestion in suggest_json['completions']:
        matches.append(suggestion["text"])
    return matches


def load_session(command_line):
    command = command_line.replace('%%flink_sql', '')
    args = parse_argstring(VvpMagics.flink_sql, command)
    session_name = args.session or VvpSession.default_session_name
    if session_name is not None:
        try:
            return VvpSession.get_session(session_name)
        except SessionException:
            return None
    return None


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