#!/bin/sh

USAGE="Usage: $0 <PLAYBOOK> <OPENSHIFT_PROVISION_CLUSTER_NAME>"
PLAYBOOK="$1"
export OPENSHIFT_PROVISION_CLUSTER_NAME="$2"

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

find_cluster_main () {
  for EXT in json yaml yml; do
    CONF="$OPENSHIFT_PROVISION_CONFIG_PATH/cluster/$OPENSHIFT_PROVISION_CLUSTER_NAME/vars/main.$EXT"
    if [[ -f "$CONF" ]]; then
      echo "$CONF"
      return
    fi
  done
  errexit "Unable to find cluster main config at any of" \
    "$OPENSHIFT_PROVISION_CONFIG_PATH/cluster/$OPENSHIFT_PROVISION_CLUSTER_NAME/vars/main.json" \
    "$OPENSHIFT_PROVISION_CONFIG_PATH/cluster/$OPENSHIFT_PROVISION_CLUSTER_NAME/vars/main.yaml" \
    "$OPENSHIFT_PROVISION_CONFIG_PATH/cluster/$OPENSHIFT_PROVISION_CLUSTER_NAME/vars/main.yml"
}

[[ -z "$PLAYBOOK" ]] && errexit "No PLAYBOOK provided."
[[ -z "$OPENSHIFT_PROVISION_CLUSTER_NAME" ]] && errexit "No OPENSHIFT_PROVISION_CLUSTER_NAME provided."

# Location of openshift-ansible
OPENSHIFT_ANSIBLE_PATH=${OPENSHIFT_ANSIBLE_PATH:-/usr/share/ansible/openshift-ansible}

# Path to the cluster config
export OPENSHIFT_PROVISION_CONFIG_PATH=${OPENSHIFT_PROVISION_CONFIG_PATH:-$PWD/../config}

# Directory within OPENSHIFT_PROVISION_CONFIG_PATH of the cluster config directoriy
OPENSHIFT_PROVISION_CLUSTER_DIR=${OPENSHIFT_PROVISION_CONFIG_PATH}/cluster/${OPENSHIFT_PROVISION_CLUSTER_NAME}

# Location of openshift-provision-demo to copy over to controller instance
OPENSHFIT_PROVISION_DEMO_DIR=$(dirname $PWD)

# Vault password file to protect any sensitive configuration
VAULT_PASSWORD_FILE=${VAULT_PASSWORD_FILE:-$PWD/../.vaultpw}

[[ -d "$OPENSHIFT_ANSIBLE_PATH" ]] || \
  errexit "OPENSHIFT_ANSIBLE_PATH not found at $OPENSHIFT_ANSIBLE_PATH"
[[ -d "$OPENSHIFT_PROVISION_CONFIG_PATH" ]] || \
  errexit "OPENSHIFT_PROVISION_CONFIG_PATH not found at $OPENSHIFT_PROVISION_CONFIG_PATH"
[[ -d "$OPENSHIFT_PROVISION_CLUSTER_DIR" ]] || \
  errexit "Cluster subdirectory not found at $OPENSHIFT_PROVISION_CLUSTER_DIR"
[[ -f "$VAULT_PASSWORD_FILE" ]] || \
  errexit "VAULT_PASSWORD_FILE not found at $VAULT_PASSWORD_FILE"

CLUSTER_MAIN_CONF="$(find_cluster_main)"

ANSIBLE_VARS="\
--inventory=../hosts.py \
--vault-password-file=$VAULT_PASSWORD_FILE \
-e openshift_provision_cluster_name=$OPENSHIFT_PROVISION_CLUSTER_NAME \
-e openshift_ansible_path=$OPENSHIFT_ANSIBLE_PATH \
-e openshift_provision_config_path=$OPENSHIFT_PROVISION_CONFIG_PATH \
-e vault_password_file=$VAULT_PASSWORD_FILE \
-e @$CLUSTER_MAIN_CONF"

export ANSIBLE_ROLES_PATH=$OPENSHFIT_PROVISION_DEMO_DIR/roles

ansible-playbook $ANSIBLE_VARS $PLAYBOOK
