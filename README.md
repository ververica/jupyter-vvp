# vvp-jupyter

[![Build Status](https://travis-ci.com/dataArtisans/vvp-jupyter.svg?token=RGozj1rgTPauwuugxzZx&branch=master)](https://travis-ci.com/dataArtisans/vvp-jupyter)

Experimental Jupyter Integration for Flink SQL via Ververica Platform

## Installation and usage

The Jupyter integration is implemented as custom magics, the code with instructions on how to build and use can be found
in the [vvp-magics](vvp-magics) folder.

## Documentation

User documentation can be found in the [vvp-magics README](vvp-magics/README.md).

Documentation for design decisions can be found in the [docs folder](docs/design)

## Docker compose setup

In order to start a docker compose cluster containing the VVP and the Jupyter notebook with the installed magics,
first build the Docker file as described in the [Readme](vvp-magics/README.md), then run
`docker-compose up vvp-gateway vvp-appmanager vvp-ui vvp-jupyter`.