#!/bin/bash
set -e

[[ -e demo.env ]] && . demo.env

USAGE="Usage: $0 <DEMO_CLUSTER_NAME>"

export DEMO_CLUSTER_NAME=${1:-$DEMO_CLUSTER_NAME}

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

[[ -z "$DEMO_CLUSTER_NAME" ]] && errexit "No DEMO_CLUSTER_NAME provided."

cd provision-controller
./ansible-playbook.sh terraform-destroy.yml $DEMO_CLUSTER_NAME
cd ..
