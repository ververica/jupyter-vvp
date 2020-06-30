#!/bin/bash

openssl aes-256-cbc -K $encrypted_6d931d8515f6_key -iv $encrypted_6d931d8515f6_iv -in ./gcp-client-secret.json.enc -out $HOME/gcp-client-secret.json -d
gcloud --quiet auth activate-service-account --key-file $HOME/gcp-client-secret.json
sudo ln -s /usr/lib/google-cloud-sdk/bin/docker-credential-gcloud /usr/bin/docker-credential-gcloud
gcloud --quiet auth configure-docker
docker push eu.gcr.io/vvp-devel-240810/vvp-jupyter:latest