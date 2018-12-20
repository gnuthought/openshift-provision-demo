#!/bin/sh
set -e

cd provision-controller
./ansible-playbook.sh configure.yml $1

cat <<EOF
Controller setup complete.
Use ssh to connect to controller to continue provisioning your OpenShift cluster.

EOF
