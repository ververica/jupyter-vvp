import json

from .httpsession import HttpSession

NAMESPACES_ENDPOINT = "/namespaces/v1/namespaces"


def get_deployment_targets_list_endpoint(namespace):
    return "/api/v1/namespaces/{}/deployment-targets".format(namespace)


def invalid_token():
    raise NotAuthorizedException("Bad token, or your credentials are not sufficient to perform this operation.")


class VvpSession:
    _sessions = {}
    default_session_name = None

    def __init__(self, vvp_base_url: str, namespace: str, api_key: str = None):
        """

        :type namespace: string
        :type vvp_base_url: string
        :type api_key: string
        """

        self._http_session = HttpSession(vvp_base_url, None, api_key)

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
    def create_session(cls, vvp_base_url, namespace, session_name, set_default=False, force=False, api_key=None):
        session = cls(vvp_base_url, namespace, api_key)
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
            200: lambda: True,
            401: invalid_token,
            403: invalid_token
        }
        return actions.get(
            response.status_code, SessionException("Error verifying namespace: code {} returned with message '{}'."
                                                   .format(response.status_code, response.text))
        )()

    def _get_namespace_info(self, namespace):
        request = self._http_session.get(NAMESPACES_ENDPOINT + "/{}".format(namespace))
        namespace = (json.loads(request.text))["namespace"]
        return namespace

    @staticmethod
    def get_namespaces(base_url, api_key=None):

        request = HttpSession(base_url, None, api_key=api_key).get(NAMESPACES_ENDPOINT)

        def return_namespaces():
            namespaces = json.loads(request.text)
            return namespaces

        actions = {
            200: return_namespaces,
            401: invalid_token,
            403: invalid_token
        }
        return actions.get(
            request.status_code, SessionException("An error occurred when obtaining namespace details")
        )()

    def submit_post_request(self, endpoint, requestbody):
        request = self._http_session.post(
            path=endpoint,
            request_headers={"Content-Type": "application/json"},
            data=requestbody
        )
        return request

    def execute_get_request(self, endpoint):
        request = self._http_session.get(path=endpoint, request_headers={"Content-Type": "application/json"})
        return request

    def get_base_url(self):
        return self._http_session.get_base_url()


class NotAuthorizedException(Exception):
    def __init__(self, message=""):
        super(NotAuthorizedException, self).__init__(message)


class SessionException(Exception):

    def __init__(self, message=""):
        super(SessionException, self).__init__(message)
