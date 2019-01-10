#!/bin/sh
cd provision-cluster
# FIXME - instead of OPENSHIFT_ROLE_FILTER, it should be exclude scaling/dynamic nodes
export OPENSHIFT_ROLE_FILTER=master,image
./ansible-playbook.sh bootstrap.yml $1
