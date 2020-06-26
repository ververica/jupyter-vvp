import json

from .httpsession import HttpSession

namespaces_endpoint = "/namespaces/v1/namespaces"


class VvpSession:
    _sessions = {}
    default_session_name = None

    def __init__(self, vvp_base_url: str, namespace: str):
        """

        :type http_session: HttpSession
        :type namespace: string
        :type vvp_base_url: string
        """

        self._http_session = HttpSession(vvp_base_url, None)

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
    def create_session(cls, vvp_base_url, namespace, session_name, set_default=False, force=False):
        session = cls(vvp_base_url, namespace)
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
        return self._get_namespace(self._namespace)

    def _is_valid_namespace(self, namespace):
        if not namespace:
            return False

        request = self._http_session.get(namespaces_endpoint + "/{}".format(namespace))
        validity_from_statuscodes = {200: True, 400: False, 404: False}
        return validity_from_statuscodes[request.status_code]

    def _get_namespace(self, namespace):
        request = self._http_session.get(namespaces_endpoint + "/{}".format(namespace))
        namespace = (json.loads(request.text))["namespace"]
        return namespace

    @staticmethod
    def get_namespaces(base_url):
        print("Requesting from {}...".format(base_url + namespaces_endpoint))
        request = HttpSession(base_url, None).get(namespaces_endpoint)
        namespaces = json.loads(request.text)
        return namespaces

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


class SessionException(Exception):

    def __init__(self, message=""):
        super(SessionException, self).__init__(message)
