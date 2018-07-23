#!/bin/sh

USAGE="Usage: $0 <PLAYBOOK> <CLUSTER_NAME>"
PLAYBOOK="$1"
OPENSHIFT_CLUSTER_NAME="$2"

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

[[ -z "$PLAYBOOK" ]] && errexit "No PLAYBOOK provided."
[[ -z "$OPENSHIFT_CLUSTER_NAME" ]] && errexit "No OPENSHIFT_CLUSTER_NAME provided."

OPENSHIFT_ANSIBLE_LOCATION=${OPENSHIFT_ANSIBLE_LOCATION:-~/git/github.com/openshift/openshift-ansible}
OPENSHIFT_CONFIG_LOCATION=${OPENSHIFT_CONFIG_LOCATION:-$PWD/../config}
OPENSHIFT_CLUSTER_DIR=${OPENSHIFT_CONFIG_LOCATION}/cluster/${OPENSHIFT_CLUSTER_NAME}
VAULT_PASSWORD_FILE=${VAULT_PASSWORD_FILE:-$PWD/../.vaultpw}

[[ -d "$OPENSHIFT_ANSIBLE_LOCATION" ]] || \
  errexit "OPENSHIFT_ANSIBLE_LOCATION not found at $OPENSHIFT_ANSIBLE_LOCATION"
[[ -d "$OPENSHIFT_CONFIG_LOCATION" ]] || \
  errexit "OPENSHIFT_CONFIG_LOCATION not found at $OPENSHIFT_CONFIG_LOCATION"
[[ -d "$OPENSHIFT_CLUSTER_DIR" ]] || \
  errexit "Cluster subdirectory not found at $OPENSHIFT_CLUSTER_DIR"
[[ -f "$VAULT_PASSWORD_FILE" ]] || \
  errexit "VAULT_PASSWORD_FILE not found at $VAULT_PASSWORD_FILE"

ANSIBLE_VARS="\
-e cluster_name=$OPENSHIFT_CLUSTER_NAME \
-e openshift_ansible_location=$OPENSHIFT_ANSIBLE_LOCATION \
-e openshift_config_location=$OPENSHIFT_CONFIG_LOCATION \
-e vault_password_file=$VAULT_PASSWORD_FILE"

for EXT in cert key ca; do
  if [[ -f "$OPENSHIFT_CLUSTER_DIR/tls/master.cert" ]]; then
    ANSIBLE_VARS="$ANSIBLE_VARS -e openshift_master_cluster_public_${EXT}file=$OPENSHIFT_CLUSTER_DIR/tls/master.${EXT}"
  fi
done

export OPENSHIFT_CONFIG_LOCATION OPENSHIFT_CLUSTER_NAME
ansible-playbook $ANSIBLE_VARS $PLAYBOOK
