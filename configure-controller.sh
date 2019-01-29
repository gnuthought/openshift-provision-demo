#!/bin/sh
set -e

USAGE="Usage: $0 <OPENSHIFT_PROVISION_CLUSTER_NAME>"

export OPENSHIFT_PROVISION_CLUSTER_NAME=${1:-$OPENSHIFT_PROVISION_CLUSTER_NAME}

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

[[ -z "$OPENSHIFT_PROVISION_CLUSTER_NAME" ]] && errexit "No OPENSHIFT_PROVISION_CLUSTER_NAME provided."

cd provision-controller
./ansible-playbook.sh configure.yml $OPENSHIFT_PROVISION_CLUSTER_NAME
cd ..

HOSTS_JSON=$(./hosts.py --list)
CONTROLLER_HOSTNAME=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_provision_controller_hostname')
CONTROLLER_PORT=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_provision_controller_ansible_port')
CONTROLLER_USER=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_provision_controller_ansible_user')

cat <<EOF

Controller setup complete for $OPENSHIFT_PROVISION_CLUSTER_NAME.
Use ssh to connect to controller to continue provisioning your OpenShift cluster.

ssh -p$CONTROLLER_PORT $CONTROLLER_USER@$CONTROLLER_HOSTNAME

A gitlab server has been configured at:

http://$CONTROLLER_HOSTNAME/

EOF
