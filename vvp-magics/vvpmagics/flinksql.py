import json

from pandas import DataFrame


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
    return response.status_code != 200 \
           or json.loads(response.text)['validationResult'] not in sql_validate_possible_responses


def is_supported_in(responses, response):
    return json.loads(response.text)['validationResult'] in responses


def run_query(session, cell):
    validation_response = _validate_sql(cell, session)
    if is_invalid_request(validation_response):
        raise FlinkSqlRequestException("Bad HTTP request or incompatible VVP back-end.", sql=cell)
    if is_supported_in(ddl_responses, validation_response):
        execute_command_response = _execute_sql(cell, session)
        json_data = json.loads(execute_command_response.text)
        return _json_convert_to_dataframe(json_data)
    if is_supported_in(dml_responses, validation_response):
        target = _get_deployment_target(session)
        deployment_creation_response = _create_deployment(cell, session, target)
        deployment_id = json.loads(deployment_creation_response.text)['metadata']['id']
        deployment_endpoint = sql_deployment_endpoint(session.get_namespace(), deployment_id)
        base_url = session.get_base_url()
        return base_url + deployment_endpoint

    else:
        raise SqlSyntaxException("Invalid or unsupported SQL statement.", sql=cell, response=validation_response)


def _validate_sql(cell, session):
    validate_endpoint = sql_validate_endpoint(session.get_namespace())
    body = json.dumps({"script": cell})
    validation_response = session.submit_post_request(validate_endpoint, body)
    return validation_response


def _json_convert_to_dataframe(json_data):
    if "resultTable" not in json_data:
        return json_data

    table = json_data["resultTable"]
    headers = table["headers"]
    rows = table["rows"]
    columns = []
    for h in headers:
        for v in h.values():
            columns.append(v)

    data = []
    for row in rows:
        cells = row["cells"]
        cellData = []
        for cell in cells:
            for cellValue in cell.values():
                cellData.append(cellValue)
        data.append(cellData)

    return DataFrame(data=data, columns=columns)


def _execute_sql(cell, session):
    execute_endpoint = sql_execute_endpoint(session.get_namespace())
    body = json.dumps({"statement": cell})
    execute_response = session.submit_post_request(execute_endpoint, body)
    return execute_response


def _get_deployment_target(session):
    endpoint = deployment_defaults_endpoint(session.get_namespace())
    response = session.execute_get_request(endpoint)
    return json.loads(response.text)['spec']['deploymentTargetId']


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


class SqlSyntaxException(Exception):

    def __init__(self, message="", sql=None, response=None):
        self.message = message
        self.sql = sql
        self.details = json.loads((response and response.text) or "{}")

    def get_details(self):
        return self.details


class FlinkSqlRequestException(Exception):

    def __init__(self, message="", sql=None):
        self.message = message
        self.sql = sql
