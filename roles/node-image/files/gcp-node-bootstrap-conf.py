#!/usr/bin/env python

import json
import re
import time
import traceback
import urllib2
import yaml

def get_metadata_attributes():
    while True:
        try:
            request = urllib2.Request(
                'http://metadata.google.internal/computeMetadata/v1/instance/attributes/?recursive=true',
                headers = { "Metadata-Flavor": "Google" }
            )
            return json.loads(urllib2.urlopen(request).read())
        except Exception:
            traceback.print_exec()
            time.sleep(10)

def get_node_group(metadata_attributes):
    return metadata_attributes['openshift-node-group']

def get_node_labels(metadata_attributes):
    """
    Return node labels dict parsed from kube-env metadata.

    We expect the kube-env to be valid YAML data including a line of the format:

    AUTOSCALER_ENV_VARS: kube_reserved=cpu=200m,memory=200Mi;node_labels=role=foo,foo=bar;node_taints=;

    This example should return: [ "role=foo", "foo=bar" }

    If node labels are not found, then return: [ "node-role.kubernetes.io/compute=true" ]
    """
    kube_env = yaml.load(metadata_attributes.get('kube-env', '{}'))
    autoscaler_env_vars = kube_env.get('AUTOSCALER_ENV_VARS', '')
    m = re.search(r'(?:^|;)node_labels=([^;]+)', autoscaler_env_vars)
    if m:
        return m.group(1).split(",")
    else:
        return [ "node-role.kubernetes.io/compute=true" ]

def set_node_labels(node_labels):
    node_config = yaml.load(open('/etc/origin/node/node-config.yaml', 'r'))
    print(node_config)
    node_config['kubeletArguments']['node-labels'] = node_labels
    open('/etc/origin/node/node-config.yaml', 'w').write(yaml.dump(node_config))

def set_bootstrap_config_name_in(filename, node_group):
    try:
        node_sysconfig = open(filename, 'r').read()
        open(filename, 'w').write(re.sub(
           r'BOOTSTRAP_CONFIG_NAME=.*',
           'BOOTSTRAP_CONFIG_NAME=node-config-' + node_group,
           node_sysconfig
        ))
    except IOError:
        pass

def set_bootstrap_config_name(node_group):
    set_bootstrap_config_name_in('/etc/sysconfig/origin-node', node_group)
    set_bootstrap_config_name_in('/etc/sysconfig/atomic-openshift-node', node_group)

def main():
    metadata_attributes = get_metadata_attributes()
    node_group = get_node_group(metadata_attributes)
    node_labels = get_node_labels(metadata_attributes)
    print(node_group)
    print(node_labels)
    set_node_labels(node_labels)
    set_bootstrap_config_name(node_group)

if __name__ == '__main__':
    main()
