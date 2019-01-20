#!/bin/sh
set -e

export OPENSHIFT_PROVISION_CLUSTER_NAME=${1:-$OPENSHIFT_PROVISION_CLUSTER_NAME}

cd provision-controller
./ansible-playbook.sh configure.yml $OPENSHIFT_PROVISION_CLUSTER_NAME
cd ..

HOSTS_JSON=$(./hosts.py --list)
CONTROLLER_NAME=$(echo $HOSTS_JSON | jq -r '.controller.hosts[0]')
CONTROLLER_IP=$(echo $HOSTS_JSON | jq -r "._meta.hostvars.\"$CONTROLLER_NAME\".ansible_host")
CONTROLLER_PORT=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_provision_controller_ansible_port')
CONTROLLER_USER=$(echo $HOSTS_JSON | jq -r '.all.vars.openshift_provision_controller_ansible_user')

cat <<EOF

Controller setup complete for $OPENSHIFT_PROVISION_CLUSTER_NAME.
Use ssh to connect to controller to continue provisioning your OpenShift cluster.

ssh -p$CONTROLLER_PORT $CONTROLLER_USER@$CONTROLLER_IP

EOF
