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

  --create-node-image  Create cluster image from image instance
  --host               Ansible inventory host facts
  --list               Ansible inventory host list
  --scaleup            Scale up dynamic components to minimum
  --wait               Wait for vms to start

Environment Variables:
OPENSHIFT_CONFIG_LOCATION - Location of cluster configuration
OPENSHIFT_CLUSTER_NAME - Name of cluster in configuration
""",
    file=sys.stderr)
    sys.exit(1)

def main():
    if( 'OPENSHIFT_CLUSTER_NAME' not in os.environ ):
        exit_usage('OPENSHIFT_CLUSTER_NAME environment variable not set.')

    ocpinv = OpenShiftInventory(
        cluster_name = os.environ['OPENSHIFT_CLUSTER_NAME'],
        config_dir = os.environ.get('OPENSHIFT_CONFIG_LOCATION', 'config')
    )

    # FIXME - allow debug level to be set for logger
    #logging.basicConfig(level=logging.INFO)

    if len(sys.argv) == 2 and sys.argv[1] == '--create-node-image':
        ocpinv.create_node_image()
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        ocpinv.print_host_json(sys.argv[2])
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
