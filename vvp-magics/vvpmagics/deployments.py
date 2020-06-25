import json

from IPython.core.display import display, HTML, clear_output
from ipywidgets import widgets

NO_DEFAULT_DEPLOYMENT_MESSAGE = "No default deployment target found."


def deployment_defaults_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-defaults".format(namespace)


def sql_deployment_create_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployments".format(namespace)


def sql_deployment_endpoint(namespace, deployment_id):
    return "/api/v1/namespaces/{}/deployments/{}".format(namespace, deployment_id)


def vvp_deployment_detail_endpoint(namespace, deployment_id):
    return "/app/#/namespaces/{}/deployments/{}/detail/overview".format(namespace, deployment_id)


deployment_states = {
    "warning": ["CANCELLED", "SUSPENDED"],
    "success": ["RUNNING", "FINISHED"],
    "info": ["TRANSITIONING"],
    "danger": ["FAILED"]
}


def all_deployment_states():
    return [state for states in deployment_states.values() for state in states]


def make_deployment(cell, session):
    target = _get_deployment_target(session)
    deployment_creation_response = _create_deployment(cell, session, target)
    deployment_id = json.loads(deployment_creation_response.text)['metadata']['id']
    _show_output(deployment_id, session)
    return deployment_id


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
    if (not state) or state not in all_deployment_states():
        raise DeploymentStateException("Could not obtain valid deployment state for deployment {}."
                                       .format(deployment_id))
    return state


def _show_output(deployment_id, session):
    status_output = widgets.Output()
    link_output = widgets.Output()

    def get_button_style(state):
        for key in deployment_states.keys():
            if state in deployment_states[key]:
                return key
        return "info"

    def update_button(b):
        with status_output:
            button.disabled = True
            clear_output(wait=True)
            print("Getting status...")
            try:
                state = _get_deployment_state(deployment_id, session)
            except DeploymentStateException as exception:
                button.disabled = False
                raise exception
            clear_output(wait=True)
            print("Status: {}.".format(state))
            button.button_style = get_button_style(state)
            button.disabled = False

    button = widgets.Button(
        description="Refresh",
        disabled=False,
        button_style="info",  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Click to refresh deployment status',
        icon='refresh'
    )
    button.on_click(update_button)

    deployment_endpoint = vvp_deployment_detail_endpoint(session.get_namespace(), deployment_id)
    url = session.get_base_url() + deployment_endpoint
    with link_output:
        display(
            HTML("""[<a href="{}" target="_blank">Click here to see the deployment in the platform.</a>]"""
                 .format(url)))
    with status_output:
        print("Click button to update deployment status.")
    display(widgets.HBox(children=(button, status_output, link_output)))


class VvpConfigurationException(Exception):

    def __init__(self, message="", sql=None):
        super(VvpConfigurationException, self).__init__(message)
        self.sql = sql


class DeploymentStateException(Exception):
    def __init__(self, message="", sql=None):
        super(DeploymentStateException, self).__init__(message)
        self.sql = sql
