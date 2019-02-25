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

# FIXME - instead of OPENSHIFT_ROLE_FILTER, it should be exclude scaling/dynamic nodes
export OPENSHIFT_ROLE_FILTER=master,image

cd provision-cluster
./ansible-playbook.sh configure.yml $1
cd ..

HOSTS_JSON=$(./hosts.py --list)
MASTER_PUBLIC_HOSTNAME=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_master_cluster_public_hostname')

cat <<EOF

Cluster configuration complete for $DEMO_CLUSTER_NAME.

You may access the console at https://$MASTER_PUBLIC_HOSTNAME/

EOF
