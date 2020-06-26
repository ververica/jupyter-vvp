import json

from IPython.core.display import display, HTML

NO_DEFAULT_DEPLOYMENT_MESSAGE = "No default deployment target found."


def deployment_defaults_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-defaults".format(namespace)


def sql_deployment_create_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployments".format(namespace)


def sql_deployment_endpoint(namespace, deployment_id):
    return "/api/v1/namespaces/{}/deployments/{}".format(namespace, deployment_id)


def vvp_deployment_detail_endpoint(namespace, deployment_id):
    return "/app/#/namespaces/{}/deployments/{}/detail/overview".format(namespace, deployment_id)


deployment_states_warn = ["CANCELLED", "SUSPENDED"]
deployment_states_good = ["RUNNING, FINISHED"]
deployment_states_info = ["TRANSITIONING"]
deployment_states_bad = ["FAILED"]
deployment_states = deployment_states_bad + deployment_states_good + deployment_states_info + deployment_states_warn


def make_deployment(cell, session):
    target = _get_deployment_target(session)
    deployment_creation_response = _create_deployment(cell, session, target)
    deployment_id = json.loads(deployment_creation_response.text)['metadata']['id']
    _show_url(deployment_id, session)
    return _get_deployment_state(deployment_id, session)


def _get_deployment_target(session):
    endpoint = deployment_defaults_endpoint(session.get_namespace())
    response = session.execute_get_request(endpoint)
    deployment_target_id = json.loads(response.text)["spec"].get("deploymentTargetId")
    if deployment_target_id is None:
        raise VvpConfigurationException(NO_DEFAULT_DEPLOYMENT_MESSAGE)
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


def _get_deployment_data(deployment_id, session):
    deployment_endpoint = sql_deployment_endpoint(session.get_namespace(), deployment_id)
    return json.loads(session.execute_get_request(deployment_endpoint).text)


def _get_deployment_state(deployment_id, session):
    data = _get_deployment_data(deployment_id, session)
    state = data.get("status", {}).get("state")
    if not state or state not in deployment_states:
        raise Exception("Unknown deployment state.")
    return state


def _show_url(deployment_id, session):
    deployment_endpoint = vvp_deployment_detail_endpoint(session.get_namespace(), deployment_id)
    url = session.get_base_url() + deployment_endpoint
    display(HTML("""<a href="{}" target="_blank">Deployment link</a>""".format(url)))


class VvpConfigurationException(Exception):

    def __init__(self, message="", sql=None):
        super(VvpConfigurationException, self).__init__(message)
        self.sql = sql
