# 4 - Testing

## Context
As the notebooks will run on the users machine, errors will be very hard to find and debug, thus automated tests should
be used as much as possible.

## Decision
Simple unit tests should be used where applicable, using mocks to replace calls to VVP.
Additionally there will be a few tests that run against a locally deployed VVP to test integration.
There is also a test that will execute the example Notebooks and check if they pass, also connecting to a locally
deployed VVP.
The integration tests will not be executed on TravisCI for now, but this could be added, e.g. using the docker-compose
setup.