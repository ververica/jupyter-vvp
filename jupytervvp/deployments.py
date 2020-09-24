import json

from jupytervvp.deploymentapiconstants import sql_deployment_create_endpoint, deployment_defaults_endpoint
from jupytervvp.deploymentoutput import DeploymentOutput

NO_DEFAULT_DEPLOYMENT_MESSAGE = "No default deployment target found."
VVP_DEFAULT_PARAMETERS_VARIABLE = "vvp_default_parameters"

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
            DeploymentOutput(deployment_id, session).show_output()
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
    def get_deployment_parameters(shell, args):
        if shell is None:
            return None

        parameters_variable = VVP_DEFAULT_PARAMETERS_VARIABLE
        if args.parameters is not None:
            parameters_variable = args.parameters
        return shell.user_ns.get(parameters_variable, None)


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
