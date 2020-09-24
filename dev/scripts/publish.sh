#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

cd "$(dirname "$0")"

pip install -r requirements.txt

cd ../..
python setup.py sdist
twine check dist/*
twine upload dist/*