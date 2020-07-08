import json

from IPython.core.display import display, HTML, clear_output
from ipywidgets import widgets

NO_DEFAULT_DEPLOYMENT_MESSAGE = "No default deployment target found."
VVP_DEFAULT_PARAMETERS_VARIABLE = "vvp_default_parameters"


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


REQUIRED_DEFAULT_PARAMETERS = {
    "metadata.annotations.license/testing": False
}

NON_PARSABLE_DEPLOYMENT_SETTINGS = [
    "metadata.annotations",
    "spec.template.metadata.annotations",
    "spec.template.spec.flinkConfiguration",
    "spec.template.spec.logging.log4jLoggers"
]


class Deployments:

    @classmethod
    def make_deployment(cls, cell, session, shell, args):
        parameters = cls.get_deployment_parameters(shell, args)
        endpoint = sql_deployment_create_endpoint(session.get_namespace())
        body = cls._build_deployment_request(cell, session, parameters)
        deployment_creation_response = session.submit_post_request(endpoint=endpoint, requestbody=json.dumps(body))
        if deployment_creation_response.status_code == 201:
            deployment_id = json.loads(deployment_creation_response.text)['metadata']['id']
            cls._show_output(deployment_id, session)
            return deployment_id
        return cls.handle_deployment_error(deployment_creation_response)

    @classmethod
    def handle_deployment_error(cls, deployment_creation_response):
        status_code = deployment_creation_response.status_code
        response_body = json.loads(deployment_creation_response.text)
        if status_code == 400:
            raise DeploymentException(message="There was an error creating the deployment.", response=response_body)
        else:
            raise DeploymentException(message="There was an error creating the deployment: status code {}."
                                      .format(status_code))

    @staticmethod
    def _get_deployment_target(session):
        endpoint = deployment_defaults_endpoint(session.get_namespace())
        response = session.execute_get_request(endpoint)
        deployment_target_id = json.loads(response.text)["spec"].get("deploymentTargetId")
        if deployment_target_id is None:
            raise VvpConfigurationException(NO_DEFAULT_DEPLOYMENT_MESSAGE)
        return deployment_target_id

    @classmethod
    def _build_deployment_request(cls, cell, session, override_parameters):
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
        cls.set_values_from_flat_parameters(base_body, REQUIRED_DEFAULT_PARAMETERS)

        if override_parameters is not None:
            cls.set_values_from_flat_parameters(base_body, override_parameters)
            cls.set_all_special_case_parameters(base_body, override_parameters)

        return base_body

    @classmethod
    def set_values_from_flat_parameters(cls, base_body, parameters):
        try:
            for key in parameters.keys():
                for special_case in NON_PARSABLE_DEPLOYMENT_SETTINGS:
                    if key.startswith(special_case):
                        return
                cls._set_value_from_flattened_key(base_body, parameters, key)
        except VvpParameterException as exception:
            raise exception
        except Exception as exception:
            raise VvpParameterException("Error converting parameters for job submission. "
                                        "Your parameters may be invalid. "
                                        "({})".format(exception.__str__()))

    @classmethod
    def set_all_special_case_parameters(cls, base_body, override_parameters):
        for special_case_prefix in NON_PARSABLE_DEPLOYMENT_SETTINGS:
            cls._set_special_case_parameters(base_body, special_case_prefix, override_parameters)

    @classmethod
    def _set_special_case_parameters(cls, base_body, prefix, parameters):
        for key in parameters.keys():
            if key.startswith(prefix):
                keys_chain = prefix.split(".")
                key_end = key[len(prefix + "."):]
                keys_chain.append(key_end)
                cls._set_value_in_dict_from_keys(base_body, keys_chain, parameters[key])

    @classmethod
    def _set_value_from_flattened_key(cls, dictionary, parameters, flattened_key):
        value = parameters.get(flattened_key)
        keys = flattened_key.split(".")
        cls._set_value_in_dict_from_keys(dictionary, keys, value)

    @classmethod
    def _set_value_in_dict_from_keys(cls, dictionary, keys, value):
        if len(keys) == 1:
            dictionary[keys[0]] = value
        else:
            try:
                if not dictionary.get(keys[0]):
                    dictionary[keys[0]] = {}
                cls._set_value_in_dict_from_keys(dictionary[keys[0]], keys[1:], value)
            except AttributeError as exception:
                raise VvpParameterException("Bad parameters {} , {} ".format(keys, value) +
                                            ": you may be trying to set a sub-key value on an already set scalar. ")

    @staticmethod
    def _get_deployment_data(deployment_id, session):
        deployment_endpoint = sql_deployment_endpoint(session.get_namespace(), deployment_id)
        return json.loads(session.execute_get_request(deployment_endpoint).text)

    @staticmethod
    def get_deployment_parameters(shell, args):
        if shell is None:
            return None

        parameters_variable = VVP_DEFAULT_PARAMETERS_VARIABLE
        if args.parameters is not None:
            parameters_variable = args.parameters
        return shell.user_ns.get(parameters_variable, None)

    @classmethod
    def _get_deployment_state(cls, deployment_id, session):
        data = cls._get_deployment_data(deployment_id, session)
        state = data.get("status", {}).get("state")
        if (not state) or state not in all_deployment_states():
            raise DeploymentStateException("Could not obtain valid deployment state for deployment {}."
                                           .format(deployment_id))
        return state

    @classmethod
    def _cancel_deployment(cls, deployment_id, session):
        body = {"spec": {"state": "CANCELLED"}}
        url = "/api/v1/namespaces/{}/deployments/{}".format(session.get_namespace(), deployment_id)
        session.submit_patch_request(url, json.dumps(body))

    @classmethod
    def _delete_deployment(cls, deployment_id, session):
        url = "/api/v1/namespaces/{}/deployments/{}".format(session.get_namespace(), deployment_id)
        session.execute_delete_request(url)

    @classmethod
    def _show_output(cls, deployment_id, session):
        status_output = widgets.Output()
        link_output = widgets.Output()

        def get_status_button_style(state):
            for key in deployment_states.keys():
                if state in deployment_states[key]:
                    return key
            return "info"

        def update_status_button(b):
            with status_output:
                status_button.disabled = True
                clear_output(wait=True)
                print("Getting status...")
                try:
                    state = cls._get_deployment_state(deployment_id, session)
                    if state == "CANCELLED":
                        delete_button.disabled = False
                    cancel_button.state = True
                except DeploymentStateException as exception:
                    status_button.disabled = False
                    clear_output(wait=True)
                    print("Couldn't get deployment state.")
                    delete_button.disabled = True
                    cancel_button.disabled = True
                    return
                clear_output(wait=True)
                print("Status: {}.".format(state))
                status_button.button_style = get_status_button_style(state)
                status_button.disabled = False

        def cancel_deployment(b):
            cls._cancel_deployment(deployment_id, session)

        def delete_deployment(b):
            cls._delete_deployment(deployment_id, session)

        status_button = widgets.Button(
            description="Refresh",
            disabled=False,
            button_style="info",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip='Click to refresh deployment status',
            icon='refresh'
        )
        status_button.on_click(update_status_button)
        cancel_button = widgets.Button(
            description="Cancel",
            disabled=False,
            button_style="warning",
            tooltip='Cancel the deployment',
            icon="cancel"
        )
        cancel_button.on_click(cancel_deployment)
        delete_button = widgets.Button(
            description="Delete",
            disabled=True,
            button_style="danger",
            tooltip='Delete the deployment (only when in cancelled state).',
            icon="trash"
        )
        delete_button.on_click(delete_deployment)

        deployment_endpoint = vvp_deployment_detail_endpoint(session.get_namespace(), deployment_id)
        url = session.get_base_url() + deployment_endpoint

        with link_output:
            display(
                HTML("""[<a href="{}" target="_blank">Link to deployment in the platform.</a>]"""
                     .format(url)))
        with status_output:
            print("Status: click 'refresh'.")
        display(widgets.HBox(children=(status_button, status_output, cancel_button, delete_button, link_output)))


class DeploymentException(Exception):
    def __init__(self, message="", sql=None, response=None):
        super(DeploymentException, self).__init__(message)
        self.sql = sql
        self.response = response


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
