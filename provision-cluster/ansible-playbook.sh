#!/bin/sh

USAGE="Usage: $0 <PLAYBOOK> <OPENSHIFT_CLUSTER_NAME>"
PLAYBOOK="$1"
OPENSHIFT_CLUSTER_NAME="$2"

errexit () {
  echo -e "$1\n$USAGE" >&2
  exit 1
}

find_cluster_main () {
  for EXT in json yaml yml; do
    CONF="$OPENSHIFT_CONFIG_LOCATION/cluster/$OPENSHIFT_CLUSTER_NAME/vars/main.$EXT"
    if [[ -f "$CONF" ]]; then
      echo "$CONF"
      return
    fi
  done
  errexit "Unable to find cluster main config at any of" \
    "$OPENSHIFT_CONFIG_LOCATION/cluster/$OPENSHIFT_CLUSTER_NAME/vars/main.json" \
    "$OPENSHIFT_CONFIG_LOCATION/cluster/$OPENSHIFT_CLUSTER_NAME/vars/main.yaml" \
    "$OPENSHIFT_CONFIG_LOCATION/cluster/$OPENSHIFT_CLUSTER_NAME/vars/main.yml"
}

[[ -z "$PLAYBOOK" ]] && errexit "No PLAYBOOK provided."
[[ -z "$OPENSHIFT_CLUSTER_NAME" ]] && errexit "No OPENSHIFT_CLUSTER_NAME provided."

# Location of openshift-ansible
OPENSHIFT_ANSIBLE_LOCATION=${OPENSHIFT_ANSIBLE_LOCATION:-/usr/share/ansible/openshift-ansible}

# Path to the cluster config
OPENSHIFT_CONFIG_LOCATION=${OPENSHIFT_CONFIG_LOCATION:-$PWD/../config}

# Directory within OPENSHIFT_CONFIG_LOCATION of the cluster config directoriy
OPENSHIFT_CLUSTER_DIR=${OPENSHIFT_CONFIG_LOCATION}/cluster/${OPENSHIFT_CLUSTER_NAME}

# Location of openshift-provision-demo to copy over to controller instance
OPENSHFIT_PROVISION_DEMO_DIR=$(dirname $PWD)

# Vault password file to protect any sensitive configuration
VAULT_PASSWORD_FILE=${VAULT_PASSWORD_FILE:-$PWD/../.vaultpw}

[[ -d "$OPENSHIFT_ANSIBLE_LOCATION" ]] || \
  errexit "OPENSHIFT_ANSIBLE_LOCATION not found at $OPENSHIFT_ANSIBLE_LOCATION"
[[ -d "$OPENSHIFT_CONFIG_LOCATION" ]] || \
  errexit "OPENSHIFT_CONFIG_LOCATION not found at $OPENSHIFT_CONFIG_LOCATION"
[[ -d "$OPENSHIFT_CLUSTER_DIR" ]] || \
  errexit "Cluster subdirectory not found at $OPENSHIFT_CLUSTER_DIR"
[[ -f "$VAULT_PASSWORD_FILE" ]] || \
  errexit "VAULT_PASSWORD_FILE not found at $VAULT_PASSWORD_FILE"

CLUSTER_MAIN_CONF="$(find_cluster_main)"

ANSIBLE_ROLES_PATH=$OPENSHFIT_PROVISION_DEMO_DIR/roles

ANSIBLE_VARS="\
--inventory=../hosts.py \
--vault-password-file=$VAULT_PASSWORD_FILE \
-e cluster_name=$OPENSHIFT_CLUSTER_NAME \
-e openshift_ansible_location=$OPENSHIFT_ANSIBLE_LOCATION \
-e openshift_config_location=$OPENSHIFT_CONFIG_LOCATION \
-e vault_password_file=$VAULT_PASSWORD_FILE \
-e @$CLUSTER_MAIN_CONF"

# Add variables with cert paths
for EXTENSION in cert key ca; do
  if [[ -f "$OPENSHIFT_CLUSTER_DIR/tls/master.cert" ]]; then
    ANSIBLE_VARS="$ANSIBLE_VARS -e openshift_master_cluster_public_${EXTENSION}file=$OPENSHIFT_CLUSTER_DIR/tls/master.${EXTENSION}"
  fi
done

# FIXME - Add support for router certs

export ANSIBLE_ROLES_PATH \
       OPENSHIFT_CONFIG_LOCATION \
       OPENSHIFT_CLUSTER_NAME
ansible-playbook $ANSIBLE_VARS $PLAYBOOK
