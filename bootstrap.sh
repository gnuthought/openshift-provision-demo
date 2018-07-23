#!/bin/sh
cd provision-cluster
./ansible-playbook.sh bootstrap.yml $1
