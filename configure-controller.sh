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
./ansible-playbook.sh configure.yml
cd ..

HOSTS_JSON=$(./hosts.py --list)
CONTROLLER_HOSTNAME=$(echo $HOSTS_JSON | jq -r '.all.vars.demo_controller_public_hostname')
CONTROLLER_PORT=$(echo $HOSTS_JSON | jq -r '.all.vars.demo_controller_ansible_port')
CONTROLLER_USER=$(echo $HOSTS_JSON | jq -r '.all.vars.demo_controller_ansible_user')

cat <<EOF

Controller setup complete for $OPENSHIFT_PROVISION_CLUSTER_NAME.
Use ssh to connect to controller to continue provisioning your OpenShift cluster.

ssh -p$CONTROLLER_PORT $CONTROLLER_USER@$CONTROLLER_HOSTNAME

A gitlab server has been configured at:

http://$CONTROLLER_HOSTNAME/

EOF
