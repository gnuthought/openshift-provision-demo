#!/bin/sh
cd provision-cluster
export OPENSHIFT_ROLE_FILTER=master,image
./ansible-playbook.sh update-node-image.yml $1
