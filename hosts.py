#!/usr/bin/env python

from __future__ import print_function

import logging
import os
import sys

from openshift_inventory import OpenShiftInventory

def exit_usage(msg=''):
    print(msg + """
Usage: hosts.py --create-node-image
   Or: hosts.py --host <HOSTNAME>
   Or: hosts.py --list
   Or: hosts.py --scaleup
   Or: hosts.py --wait <TIMEOUT_SECONDS>

  --cleanup            Cleanup resources left by terraform destroy
  --create-node-image  Create cluster image from image instance
  --host               Ansible inventory host facts
  --init               Perform any needed operations to initialize for install
  --list               Ansible inventory host list
  --scaleup            Scale up dynamic components to minimum
  --wait               Wait for vms to start

Environment Variables:
OPENSHIFT_PROVISION_CONFIG_PATH - Location of cluster configuration
OPENSHIFT_PROVISION_CLUSTER_NAME - Name of cluster in configuration
""",
    file=sys.stderr)
    sys.exit(1)

def main():
    if( 'OPENSHIFT_PROVISION_CLUSTER_NAME' not in os.environ ):
        exit_usage('OPENSHIFT_PROVISION_CLUSTER_NAME environment variable not set.')

    ocpinv = OpenShiftInventory(
        cluster_name = os.environ['OPENSHIFT_PROVISION_CLUSTER_NAME'],
        config_dir = os.environ.get('OPENSHIFT_PROVISION_CONFIG_PATH', 'config'),
        init_mode = len(sys.argv) == 2 and sys.argv[1] == '--init'
    )

    # FIXME - allow debug level to be set for logger
    #logging.basicConfig(level=logging.INFO)

    if len(sys.argv) == 2 and sys.argv[1] == '--cleanup':
        ocpinv.cleanup()
    elif len(sys.argv) == 2 and sys.argv[1] == '--create-node-image':
        ocpinv.create_node_image()
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        ocpinv.print_host_json(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == '--init':
        ocpinv.init()
    elif len(sys.argv) == 2 and sys.argv[1] == '--list':
        ocpinv.print_host_list_json()
    elif len(sys.argv) == 2 and sys.argv[1] == '--scaleup':
        ocpinv.scaleup()
    elif len(sys.argv) == 3 and sys.argv[1] == '--wait':
        ocpinv.wait_for_hosts_running(int(sys.argv[2]))
    else:
        exit_usage()

if __name__ == '__main__':
    main()
