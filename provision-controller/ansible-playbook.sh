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

# Location of openshift-provision-demo to copy over to controller instance
OPENSHIFT_PROVISION_PROJECT_DIR=${OPENSHIFT_PROVISION_PROJECT_DIR:-$(dirname $PWD)}

[[ -d "$OPENSHIFT_PROVISION_PROJECT_DIR" ]] || \
  errexit "OPENSHIFT_PROVISION_PROJECT_DIR not found at $OPENSHIFT_PROVISION_PROJECT_DIR"

CLUSTER_MAIN_VARS="$(find_main_vars "config/cluster/$DEMO_CLUSTER_NAME")"

# Export OPENSHIFT_PROVISION_PROJECT_DIR for use by the dynamic inventory
export OPENSHIFT_PROVISION_PROJECT_DIR

ANSIBLE_VARS=(
  '--inventory=../hosts.py'
  '-e' "openshift_provision_project_dir='$OPENSHIFT_PROVISION_PROJECT_DIR'"
  '-e' "@$OPENSHIFT_PROVISION_PROJECT_DIR/$CLUSTER_MAIN_VARS"
)

export ANSIBLE_ROLES_PATH="$OPENSHIFT_PROVISION_PROJECT_DIR/roles:~/.ansible/roles"

ansible-playbook "${ANSIBLE_VARS[@]}" $PLAYBOOK
