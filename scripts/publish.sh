#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

cd "$(dirname "$0")"

pip3 install -r requirements.txt
twine check ../dist/*
twine upload ../dist/*