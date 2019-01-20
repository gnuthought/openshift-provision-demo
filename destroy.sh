#!/bin/sh
set -e

USAGE="Usage: $0 <OPENSHIFT_PROVISION_CLUSTER_NAME>"

export OPENSHIFT_PROVISION_CLUSTER_NAME=${1:-$OPENSHIFT_PROVISION_CLUSTER_NAME}

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

[[ -z "$OPENSHIFT_PROVISION_CLUSTER_NAME" ]] && errexit "No OPENSHIFT_PROVISION_CLUSTER_NAME provided."

cd provision-cluster
./ansible-playbook.sh terraform-destroy.yml $1
