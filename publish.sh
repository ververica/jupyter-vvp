#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

cd "$(dirname "$0")"

pip install twine
twine check dist/*
twine upload dist/*