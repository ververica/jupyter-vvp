import json

from IPython.core.display import HTML, display

from vvpmagics.jsonconversion import json_convert_to_dataframe

NO_DEFAULT_DEPLOYMENT_MESSAGE = "No default deployment target found."


def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


def deployment_defaults_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-defaults".format(namespace)


def sql_deployment_create_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployments".format(namespace)


def sql_deployment_endpoint(namespace, deployment_id):
    return "/api/v1/namespaces/{}/deployments/{}".format(namespace, deployment_id)


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


def run_query(session, cell):
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
        target = _get_deployment_target(session)
        deployment_creation_response = _create_deployment(cell, session, target)
        deployment_id = json.loads(deployment_creation_response.text)['metadata']['id']
        deployment_endpoint = _get_and_show_url(deployment_id, session)
        return _get_deployment_data(deployment_endpoint, session)

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


def _get_deployment_target(session):
    endpoint = deployment_defaults_endpoint(session.get_namespace())
    response = session.execute_get_request(endpoint)
    deployment_target_id = json.loads(response.text)["spec"].get("deploymentTargetId")
    if deployment_target_id is None:
        raise FlinkSqlRequestException(NO_DEFAULT_DEPLOYMENT_MESSAGE)
    return deployment_target_id


def _create_deployment(cell, session, target):
    endpoint = sql_deployment_create_endpoint(session.get_namespace())
    deployment_name = cell
    body = {
        "metadata": {
            "name": deployment_name,
            "annotations": {"license/testing": False}
        },
        "spec": {
            "deploymentTargetId": target,
            "template": {
                "spec": {
                    "artifact": {
                        "kind": "SQLSCRIPT",
                        "sqlScript": cell
                    }
                }
            }
        }
    }
    return session.submit_post_request(endpoint=endpoint, requestbody=json.dumps(body))


def _get_deployment_data(deployment_endpoint, session):
    return json.loads(session.execute_get_request(deployment_endpoint).text)


def _get_and_show_url(deployment_id, session):
    deployment_endpoint = sql_deployment_endpoint(session.get_namespace(), deployment_id)
    url = session.get_base_url() + deployment_endpoint
    display(HTML("""<a href="{}">Deployment link</a>""".format(url)))
    return deployment_endpoint


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
