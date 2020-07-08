import json

from vvpmagics.deployments import Deployments
from vvpmagics.jsonconversion import json_convert_to_dataframe
from vvpmagics.variablesubstitution import VvpFormatter


def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


def sql_complete_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:suggest".format(namespace)


ddl_responses = [
    "VALIDATION_RESULT_VALID_DDL_STATEMENT",
    "VALIDATION_RESULT_VALID_COMMAND_STATEMENT"
]
dml_responses = [
    "VALIDATION_RESULT_VALID_INSERT_QUERY"
]
sql_validate_possible_responses = \
    ddl_responses + \
    dml_responses + \
    [
        "VALIDATION_RESULT_INVALID",
        "VALIDATION_RESULT_INVALID_QUERY",
        "VALIDATION_RESULT_UNSUPPORTED_QUERY",
        "VALIDATION_RESULT_VALID_SELECT_QUERY"
    ]


def is_invalid_request(response):
    return response['validationResult'] not in sql_validate_possible_responses


def is_supported_in(responses, response):
    return response['validationResult'] in responses


def run_query(session, raw_cell, shell, args):
    cell = VvpFormatter(raw_cell, shell.user_ns).substitute_user_variables()
    validation_response = _validate_sql(cell, session)
    if validation_response.status_code != 200:
        raise FlinkSqlRequestException("Bad HTTP request, return code {}".format(validation_response.status_code),
                                       sql=cell)
    json_response = json.loads(validation_response.text)
    if is_invalid_request(json_response):
        raise FlinkSqlRequestException("Unknown validation result: {}".format(json_response['validationResult']),
                                       sql=cell)
    if is_supported_in(ddl_responses, json_response):
        execute_command_response = _execute_sql(cell, session)
        json_data = json.loads(execute_command_response.text)
        return json_convert_to_dataframe(json_data)
    if is_supported_in(dml_responses, json_response):
        return Deployments.make_deployment(cell, session, shell, args)

    else:
        error_message = json_response['errorDetails']['message']
        raise SqlSyntaxException("Invalid or unsupported SQL statement: {}"
                                 .format(error_message), sql=cell, response=validation_response)


def _validate_sql(cell, session):
    validate_endpoint = sql_validate_endpoint(session.get_namespace())
    body = json.dumps({"script": cell})
    validation_response = session.submit_post_request(validate_endpoint, body)
    return validation_response


def _execute_sql(cell, session):
    execute_endpoint = sql_execute_endpoint(session.get_namespace())
    body = json.dumps({"statement": cell})
    execute_response = session.submit_post_request(execute_endpoint, body)
    return execute_response


def complete_sql(text, cursor_pos, session):
    complete_endpoint = sql_complete_endpoint(session.get_namespace())
    body = json.dumps({"sqlScript": text, "position": cursor_pos})
    # print("Request body: " + body, file=open('dbg.log', 'a')) # dbg
    response = session.submit_post_request(complete_endpoint, body)
    return response


class SqlSyntaxException(Exception):

    def __init__(self, message="", sql=None, response=None):
        super(SqlSyntaxException, self).__init__(message)
        self.sql = sql
        self.details = json.loads((response and response.text) or "{}")

    def get_details(self):
        return self.details


class FlinkSqlRequestException(Exception):

    def __init__(self, message="", sql=None):
        super(FlinkSqlRequestException, self).__init__(message)
        self.sql = sql
