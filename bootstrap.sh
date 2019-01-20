#!/bin/sh
set -e

export OPENSHIFT_PROVISION_CLUSTER_NAME=${1:-$OPENSHIFT_PROVISION_CLUSTER_NAME}

# FIXME - instead of OPENSHIFT_ROLE_FILTER, it should be exclude scaling/dynamic nodes
export OPENSHIFT_ROLE_FILTER=master,image

cd provision-cluster
./ansible-playbook.sh bootstrap.yml $1
cd ..

. openshift-provision.sh

HOSTS_JSON=$(./hosts.py --list)
MASTER_PUBLIC_HOSTNAME=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_master_cluster_public_hostname')

cat <<EOF

Cluster bootstrap complete for $OPENSHIFT_PROVISION_CLUSTER_NAME.

You may access the console at https://$MASTER_PUBLIC_HOSTNAME/

EOF
