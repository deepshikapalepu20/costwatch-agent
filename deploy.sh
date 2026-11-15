#!/bin/bash
set -e
cd /opt/costwatch
git pull -q
sed -i "s|^DOCKER_IMAGE=.*|DOCKER_IMAGE=$1|" .env
docker compose pull app
docker compose up -d
