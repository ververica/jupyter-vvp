# 2 - Sessions

## Context

A VVP session constitutes:

1. A URL and port for the service.
2. A namespace.
3. User credentials.

For better useability:

1. It should be possible to create a session once and re-use it later.
2. The magics should select a session in a reasonable way
     that reduces the need for the user to specify the session each time.

## Discussion

### Sessions

There should be a list of sessions somewhere,
and it should be possible for the magic(s) to query this
and return a default session.
The default session could be a last-used session or an explicitly chosen default
(with the implicit default of the only session if there is only one).
In the interest of minimising commmand side-effects,
we leave the setting of a default session to the user
via an explicit command.

### Magics

In order that magics can access the session objects,
either the session objects should be set as environment variables in IPython,
or all magics should be able to discover and access the instance of the class storing the sessions.

## Solution

1. Have a class responsible for managing sessions:
    a. Store sessions in a field (dictionary text->session) so that they can be easily accessed.
    b. Also have a default session that points to one of the sessions.
        (By implication, if there is just one session, then the default must be this one.)
    c. Provide functionality to return sessions,
        returning the default if none is specified.
    d. Allow the user to change the default session.

2. Unify so that there is only one magics class.
    a. This class should instantiate and contain an instance of the sessions class on first loading.
    b. All magics will then be able to directly access the sessions class.
