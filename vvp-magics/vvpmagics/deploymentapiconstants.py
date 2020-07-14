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
