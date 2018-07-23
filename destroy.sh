#!/bin/sh
cd provision-cluster
./ansible-playbook.sh terraform-destroy.yml $1
