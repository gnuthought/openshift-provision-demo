#!/bin/bash
set -e

[[ -e ../demo.env ]] && . ../demo.env

USAGE="Usage: $0 <PLAYBOOK> <DEMO_CLUSTER_NAME>"
PLAYBOOK="$1"
export DEMO_CLUSTER_NAME="${2:-$DEMO_CLUSTER_NAME}"

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

find_main_vars () {
  DIR="$1"
  CHECKED_PATHS=()
  for EXT in json yaml yml; do
    CONF="$DIR/vars/main.$EXT"
    if [[ -f "$OPENSHIFT_PROVISION_PROJECT_DIR/$CONF" ]]; then
      echo "$CONF"
      return
    else
      CHECKED_PATHS+=($CONF)
    fi
  done
  errexit "Unable to find main vars at any of ${CHECKED_PATHS[@]}"
}

[[ -z "$PLAYBOOK" ]] && errexit "No PLAYBOOK provided."
[[ -z "$DEMO_CLUSTER_NAME" ]] && errexit "No DEMO_CLUSTER_NAME provided."

# Location of openshift-ansible
OPENSHIFT_ANSIBLE_PATH=${OPENSHIFT_ANSIBLE_PATH:-/usr/share/ansible/openshift-ansible}

# Location of openshift-provision-demo
OPENSHIFT_PROVISION_PROJECT_DIR=${OPENSHIFT_PROVISION_PROJECT_DIR:-$(dirname $PWD)}

# Vault password file to protect any sensitive configuration
VAULT_PASSWORD_FILE=${VAULT_PASSWORD_FILE:-~/.vaultpw}

[[ -d "$OPENSHIFT_ANSIBLE_PATH" ]] || \
  errexit "OPENSHIFT_ANSIBLE_PATH not found at $OPENSHIFT_ANSIBLE_PATH"
[[ -d "$OPENSHIFT_PROVISION_PROJECT_DIR" ]] || \
  errexit "OPENSHIFT_PROVISION_PROJECT_DIR not found at $OPENSHIFT_PROVISION_PROJECT_DIR"
[[ -f "$VAULT_PASSWORD_FILE" ]] || \
  errexit "VAULT_PASSWORD_FILE not found at $VAULT_PASSWORD_FILE"

CLUSTER_MAIN_VARS="$(find_main_vars "config/cluster/$DEMO_CLUSTER_NAME")"
DEFAULT_MAIN_VARS="$(find_main_vars "config/default")"


# Export OPENSHIFT_PROVISION_PROJECT_DIR for use by the dynamic inventory
export OPENSHIFT_PROVISION_PROJECT_DIR

ANSIBLE_VARS=(
  '--inventory=../hosts.py'
  "--vault-password-file=$VAULT_PASSWORD_FILE"
  '-e' "demo_openshift_ansible_path=$OPENSHIFT_ANSIBLE_PATH"
  '-e' "openshift_provision_project_dir='$OPENSHIFT_PROVISION_PROJECT_DIR'"
  '-e' "vault_password_file=$VAULT_PASSWORD_FILE"
  '-e' "@$OPENSHIFT_PROVISION_PROJECT_DIR/$CLUSTER_MAIN_VARS"
)

export ANSIBLE_ROLES_PATH="$OPENSHIFT_PROVISION_PROJECT_DIR/roles:~/.ansible/roles:/etc/ansible/roles"

ansible-playbook "${ANSIBLE_VARS[@]}" $PLAYBOOK
