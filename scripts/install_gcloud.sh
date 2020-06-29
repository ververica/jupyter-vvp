#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

if [ -z "${TRAVIS_BUILD_NUMBER:-}" ]; then
  echo >&2 "error: \$TRAVIS_BUILD_NUMBER is unset. Did you mean to run this?"
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo >&2 "error: must be run as root"
  exit 1
fi

function main() {
  export DEBIAN_FRONTEND=noninteractive
  export APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1

  # The below installations hang for a long time on "Processing triggers for man-db", but we don't
  # actually need `man` at all.
  apt-get remove -y --purge man-db

  curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list

  apt-get update
  apt-get install -y --no-install-recommends google-cloud-sdk
}

main