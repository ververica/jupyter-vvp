import json

from IPython.core.display import display, HTML, clear_output
from ipywidgets import widgets

NO_DEFAULT_DEPLOYMENT_MESSAGE = "No default deployment target found."

required_default_parameters = {
    "metadata.annotations.license/testing": False
}


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


class Deployments:

    @classmethod
    def make_deployment(cls, cell, session):
        target = cls._get_deployment_target(session)
        endpoint = sql_deployment_create_endpoint(session.get_namespace())
        body = cls._build_deployment_request(cell, session, None)
        deployment_creation_response = session.submit_post_request(endpoint=endpoint, requestbody=json.dumps(body))
        deployment_id = json.loads(deployment_creation_response.text)['metadata']['id']
        cls._show_output(deployment_id, session)
        return deployment_id

    @staticmethod
    def _get_deployment_target(session):
        endpoint = deployment_defaults_endpoint(session.get_namespace())
        response = session.execute_get_request(endpoint)
        deployment_target_id = json.loads(response.text)["spec"].get("deploymentTargetId")
        if deployment_target_id is None:
            raise VvpConfigurationException(NO_DEFAULT_DEPLOYMENT_MESSAGE)
        return deployment_target_id

    @classmethod
    def _build_deployment_request(cls, cell, session, parameters):
        base_body = {
            "metadata": {
                "annotations": {}
            },
            "spec": {
                "state": "RUNNING",
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
        base_body['metadata']['name'] = cell
        base_body['spec']['deploymentTargetId'] = cls._get_deployment_target(session)
        cls.set_values_from_parameters(base_body, required_default_parameters)

        if parameters is not None:
            cls.set_values_from_parameters(base_body, parameters)

        return base_body

    @classmethod
    def set_values_from_parameters(cls, base_body, parameters):
        try:
            for key in parameters.keys():
                cls._set_value_for_key(base_body, parameters, key)
        except VvpParameterException as exception:
            raise exception
        except Exception as exception:
            raise VvpParameterException("Error converting parameters for job submission. "
                                        "Your parameters may be invalid. "
                                        "({})".format(exception.__str__()))

    @staticmethod
    def _set_value_for_key(dictionary, parameters, flattened_key):
        value = parameters.get(flattened_key)

        def create_nested_entry(keys):
            if len(keys) == 1:
                return value
            return {keys[1]: create_nested_entry(keys[1:])}

        def set_value(sub_dictionary, keys):
            try:
                if sub_dictionary.get(keys[0]) is None:
                    sub_dictionary[keys[0]] = create_nested_entry(keys)
                else:
                    if len(keys) == 1:
                        sub_dictionary[keys[0]] = value
                    else:
                        set_value(sub_dictionary[keys[0]], keys[1:])
            except AttributeError as exception:
                raise VvpParameterException("Bad parameters: "
                                            "you may be trying to set a subkey value on an already set scalar. ")

        listed_keys = flattened_key.split(".")
        set_value(dictionary, listed_keys)

    @staticmethod
    def _get_deployment_data(deployment_id, session):
        deployment_endpoint = sql_deployment_endpoint(session.get_namespace(), deployment_id)
        return json.loads(session.execute_get_request(deployment_endpoint).text)

    @classmethod
    def _get_deployment_state(cls, deployment_id, session):
        data = cls._get_deployment_data(deployment_id, session)
        state = data.get("status", {}).get("state")
        if (not state) or state not in all_deployment_states():
            raise DeploymentStateException("Could not obtain valid deployment state for deployment {}."
                                           .format(deployment_id))
        return state

    @classmethod
    def _show_output(cls, deployment_id, session):
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
                    state = cls._get_deployment_state(deployment_id, session)
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


class VvpParameterException(Exception):

    def __init__(self, message="", sql=None):
        super(VvpParameterException, self).__init__(message)
        self.sql = sql


class DeploymentStateException(Exception):
    def __init__(self, message="", sql=None):
        super(DeploymentStateException, self).__init__(message)
        self.sql = sql
