import json
import threading
import time

from IPython.core.display import clear_output, display, HTML
from ipywidgets import widgets, Layout

from jupytervvp.deploymentapiconstants import all_deployment_states, sql_deployment_endpoint, deployment_states


def vvp_deployment_detail_endpoint(namespace, deployment_id):
    return "/app/#/namespaces/{}/deployments/{}/detail/overview".format(namespace, deployment_id)


class DeploymentOutput:

    def __init__(self, deployment_id, session):
        self.deployment_id = deployment_id
        self.session = session

    def _get_deployment_state(self):
        data = self.get_deployment_data()
        state = data.get("status", {}).get("state")
        if (not state) or state not in all_deployment_states():
            raise DeploymentStateException("Could not obtain valid deployment state for deployment {}."
                                           .format(self.deployment_id))
        return state

    def get_deployment_data(self):
        deployment_endpoint = sql_deployment_endpoint(self.session.get_namespace(), self.deployment_id)
        return json.loads(self.session.execute_get_request(deployment_endpoint).text)

    def _cancel_deployment(self):
        body = {"spec": {"state": "CANCELLED"}}
        url = "/api/v1/namespaces/{}/deployments/{}".format(self.session.get_namespace(), self.deployment_id)
        return self.session.submit_patch_request(url, json.dumps(body))

    def _start_deployment(self):
        body = {"spec": {"state": "RUNNING"}}
        url = "/api/v1/namespaces/{}/deployments/{}".format(self.session.get_namespace(), self.deployment_id)
        return self.session.submit_patch_request(url, json.dumps(body))

    def _delete_deployment(self):
        url = "/api/v1/namespaces/{}/deployments/{}".format(self.session.get_namespace(), self.deployment_id)
        return self.session.execute_delete_request(url)

    def show_output(self):
        status_output = widgets.Output(layout=Layout(width="30%"))
        link_output = widgets.Output()

        def get_status_button_style(state):
            for key in deployment_states.keys():
                if state in deployment_states[key]:
                    return key
            return "info"

        def update_loop():
            update_loop.do = True
            while update_loop.do:
                update_status()
                time.sleep(2)

        thread = threading.Thread(target=update_loop)
        thread.daemon = True

        def update_status(b=None):
            with status_output:
                clear_output(wait=True)
                try:
                    state = self._get_deployment_state()
                    if state == "CANCELLED":
                        cancel_button.disabled = True
                        start_button.disabled = False
                        delete_button.disabled = False
                    else:
                        cancel_button.disabled = False
                        delete_button.disabled = True
                except DeploymentStateException as exception:
                    clear_output(wait=True)
                    print("Couldn't get deployment state.")
                    delete_button.disabled = True
                    start_button.disabled = True
                    cancel_button.disabled = True
                    return
                clear_output()
                status_button.button_style = get_status_button_style(state)
                status_button.description = state

        def cancel_deployment(b):
            response = self._cancel_deployment()
            if response.status_code != 200:
                raise DeploymentStateException("Server did not indicate success cancelling deployment.")
            else:
                with status_output:
                    clear_output(wait=True)
                    print("Requested CANCEL.")

        def start_deployment(b):
            response = self._start_deployment()
            if response.status_code != 200:
                raise DeploymentStateException("Server did not indicate success cancelling deployment.")
            else:
                with status_output:
                    clear_output(wait=True)
                    print("Requested START.")

        def delete_deployment(b):
            response = self._delete_deployment()
            if response.status_code == 200:
                start_button.disabled = True
                cancel_button.disabled = True
                delete_button.disabled = True
                with status_output:
                    clear_output(wait=True)
                    print("Deployment DELETED.")
                    update_loop.do = False
            else:
                raise DeploymentStateException("Server did not indicate success deleting deployment.")

        status_button = widgets.Button(
            description="Transitioning",
            disabled=True,
            # style can be 'success', 'info', 'warning', 'danger' or ''
            button_style="info",
            tooltip='Shows deployment state',
            icon='refresh'
        )

        cancel_button = widgets.Button(
            description="Cancel",
            disabled=False,
            button_style="warning",
            tooltip='Cancel the deployment',
            icon="times"
        )
        cancel_button.on_click(cancel_deployment)

        start_button = widgets.Button(
            description="Start",
            disabled=True,
            button_style="success",
            tooltip='(Re)start the deployment',
            icon="play"
        )
        start_button.on_click(start_deployment)

        delete_button = widgets.Button(
            description="Delete",
            disabled=True,
            button_style="danger",
            tooltip='Delete the deployment (only when in cancelled state).',
            icon="trash"
        )
        delete_button.on_click(delete_deployment)

        deployment_endpoint = vvp_deployment_detail_endpoint(self.session.get_namespace(), self.deployment_id)
        url = self.session.get_base_url() + deployment_endpoint

        with link_output:
            display(
                HTML("""[<a href="{}" target="_blank">See the deployment in the platform.</a>]"""
                     .format(url)))
        with status_output:
            print("Status: will refresh.")
        display(widgets.HBox(children=(status_button, status_output, cancel_button, start_button, delete_button)))
        display(link_output)

        thread.start()


class DeploymentStateException(Exception):
    def __init__(self, message="", sql=None):
        super(DeploymentStateException, self).__init__(message)
        self.sql = sql
