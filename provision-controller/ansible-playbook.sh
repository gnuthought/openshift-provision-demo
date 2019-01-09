#!/bin/sh

USAGE="Usage: $0 <PLAYBOOK> <OPENSHIFT_CLUSTER_NAME>"
PLAYBOOK="$1"
OPENSHIFT_CLUSTER_NAME="$2"

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

[[ -z "$PLAYBOOK" ]] && errexit "No PLAYBOOK provided."
[[ -z "$OPENSHIFT_CLUSTER_NAME" ]] && errexit "No OPENSHIFT_CLUSTER_NAME provided."

# Path to the cluster config
OPENSHIFT_CONFIG_LOCATION=${OPENSHIFT_CONFIG_LOCATION:-$PWD/../config}

# Directory within OPENSHIFT_CONFIG_LOCATION of the cluster config directoriy
OPENSHIFT_CLUSTER_DIR=${OPENSHIFT_CONFIG_LOCATION}/cluster/${OPENSHIFT_CLUSTER_NAME}

# Location of openshift-provision-demo to copy over to controller instance
OPENSHFIT_PROVISION_DEMO_DIR=$(dirname $PWD)

# Vault password file to protect any sensitive configuration
VAULT_PASSWORD_FILE=${VAULT_PASSWORD_FILE:-$PWD/../.vaultpw}

[[ -d "$OPENSHIFT_CONFIG_LOCATION" ]] || \
  errexit "OPENSHIFT_CONFIG_LOCATION not found at $OPENSHIFT_CONFIG_LOCATION"
[[ -d "$OPENSHIFT_CLUSTER_DIR" ]] || \
  errexit "Cluster subdirectory not found at $OPENSHIFT_CLUSTER_DIR"
[[ -f "$VAULT_PASSWORD_FILE" ]] || \
  errexit "VAULT_PASSWORD_FILE not found at $VAULT_PASSWORD_FILE"

ANSIBLE_ROLES_PATH=$OPENSHFIT_PROVISION_DEMO_DIR/roles

ANSIBLE_VARS="\
--inventory=../hosts.py \
--vault-password-file=$VAULT_PASSWORD_FILE \
-e cluster_name=$OPENSHIFT_CLUSTER_NAME \
-e openshift_provision_demo_location=$OPENSHFIT_PROVISION_DEMO_DIR \
-e openshift_config_location=$OPENSHIFT_CONFIG_LOCATION \
-e vault_password_file=$VAULT_PASSWORD_FILE"

export ANSIBLE_ROLES_PATH \
       OPENSHIFT_CONFIG_LOCATION \
       OPENSHIFT_CLUSTER_NAME
ansible-playbook $ANSIBLE_VARS $PLAYBOOK
