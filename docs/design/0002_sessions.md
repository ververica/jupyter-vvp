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

## Solution

1. Store sessions in a field (dictionary) so that they can be easily accessed.
2. Also have a default session that points to one of the sessions.
   (By implication, if there is just one session, then the default must be this one.)
3. Provide functionality to return sessions,
    returning the default if none is specified.

