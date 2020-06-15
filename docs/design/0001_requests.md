# 1 - Requests

## Context

The requests library is used to communicate with the VVP REST API.
For easier testing and reuse usage of the library should be encapsulated.

## Decision

Introduce a http_session class that will hold state for a HTTP session,
and use this session to communicate with the REST API.
The session should contain no business logic, just wrap the requests library,
and allow to use the same HTTP session for all calls.
Authentication and other headers should be set during creation of the session and reused afterwards.
To create a http session the base url and headers should be set.
To make a call the endpoint and data as well as additional headers can be passed, the HTTP method will be chosen by calling a function with the same name.

Testing should be possible through use of requests_mock.
