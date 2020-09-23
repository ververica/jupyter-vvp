import json

from .httpsession import HttpSession

NAMESPACES_ENDPOINT = "/namespaces/v1/namespaces"


def get_deployment_targets_list_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-targets".format(namespace)


class VvpSession:
    _sessions = {}
    default_session_name = None

    def __init__(self, vvp_base_url: str, namespace: str, api_key: str = None, allow_self_signed_cert: bool = False):
        """

        :type namespace: string
        :type vvp_base_url: string
        :type api_key: string
        :type allow_self_signed_cert: bool
        """

        self._http_session = HttpSession(vvp_base_url, None, api_key, allow_self_signed_cert)

        if not self._is_valid_namespace(namespace):
            raise SessionException("Invalid or empty namespace specified.")
        self._namespace = namespace

    @classmethod
    def get_sessions(cls):
        return cls._sessions.keys()

    @classmethod
    def get_session(cls, session_name=None):
        try:
            return cls._sessions[session_name or cls.default_session_name]
        except KeyError:
            raise SessionException("The session name {} is invalid.".format(session_name))

    @classmethod
    def create_session(cls, vvp_base_url, namespace, session_name, set_default=False, force=False, api_key=None,
                       allow_self_signed_cert=False):
        session = cls(vvp_base_url, namespace, api_key, allow_self_signed_cert)
        cls._add_session_to_dict(session_name, session, force=force)
        if (cls.default_session_name is None) or set_default:
            cls.default_session_name = session_name
        return session

    @classmethod
    def _add_session_to_dict(cls, session_name, session, force=False):
        if (session_name in cls._sessions) and not force:
            raise SessionException("The session name {} already exists. Please use --force to update."
                                   .format(session_name))
        cls._sessions[session_name] = session

    def get_namespace(self):
        return self._namespace

    def get_namespace_info(self):
        return self._get_namespace_info(self._namespace)

    def _is_valid_namespace(self, namespace):
        if not namespace:
            return False

        response = self._http_session.get(get_deployment_targets_list_endpoint(namespace))
        actions = {
            200: lambda x: True,
            401: NotAuthorizedException.raise_invalid_token,
            403: NotAuthorizedException.raise_invalid_token,
            "unknown": SessionException.raise_namespace_validation_error
        }
        return actions.get(response.status_code, actions['unknown'])(response)

    def _get_namespace_info(self, namespace):
        request = self._http_session.get(NAMESPACES_ENDPOINT + "/{}".format(namespace))
        namespace = (json.loads(request.text))["namespace"]
        return namespace

    @staticmethod
    def get_namespaces(base_url, api_key=None):

        response = HttpSession(base_url, None, api_key=api_key).get(NAMESPACES_ENDPOINT)

        def return_namespaces():
            namespaces = json.loads(response.text)
            return namespaces

        actions = {
            200: return_namespaces,
            401: NotAuthorizedException.raise_invalid_token,
            403: NotAuthorizedException.raise_invalid_token,
            "unknown": SessionException.raise_namespace_details_error
        }
        return actions.get(response.status_code, actions['unknown'])()

    def submit_post_request(self, endpoint, requestbody):
        request = self._http_session.post(
            path=endpoint,
            request_headers={"Content-Type": "application/json"},
            data=requestbody
        )
        return request

    def submit_patch_request(self, endpoint, requestbody):
        request = self._http_session.patch(
            path=endpoint,
            request_headers={"Content-Type": "application/json"},
            data=requestbody
        )
        return request

    def execute_get_request(self, endpoint):
        request = self._http_session.get(path=endpoint, request_headers={"Content-Type": "application/json"})
        return request

    def execute_delete_request(self, endpoint):
        request = self._http_session.delete(path=endpoint)
        return request

    def get_base_url(self):
        return self._http_session.get_base_url()


class NotAuthorizedException(Exception):
    def __init__(self, message=""):
        super(NotAuthorizedException, self).__init__(message)

    @classmethod
    def raise_invalid_token(cls, response=None):
        raise cls("Bad token, or your credentials are not sufficient to perform this operation.")


class SessionException(Exception):

    def __init__(self, message=""):
        super(SessionException, self).__init__(message)

    @classmethod
    def raise_namespace_validation_error(cls, response):
        raise cls("Error verifying namespace: code {} returned with message '{}'."
                  .format(response.status_code, response.text))

    @classmethod
    def raise_namespace_details_error(cls):
        raise cls("Problem getting list of namespaces.")
