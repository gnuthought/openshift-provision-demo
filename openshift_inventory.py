#!/usr/bin/env python

import jinja2
import json
import os
import re
import six
import time
import yaml

class OpenShiftInventory:
    def __init__(
        self,
        openshift_provision_project_dir,
        cluster_name,
        init_mode=False
    ):
        self.openshift_provision_project_dir = openshift_provision_project_dir
        self.cluster_name = cluster_name
        self.init_mode = init_mode
        self.load_cluster_config()

    def load_cluster_config(self):
        openshift_provision_config_path = [
            'config/cluster/' + self.cluster_name + '/vars/main.yml',
            'config/default/vars/main.yml'
        ]
        self.cluster_config = {
            'openshift_provision_config_path': openshift_provision_config_path
        }
        conf_bootstrap = {}

        # Load config path in reverse order so that earlier entries override later ones
        for path in openshift_provision_config_path[::-1]:
            conf_bootstrap.update(self.load_vars_file(path))

        conf_hierarchy = yaml.load(
            self.value_expand(
                conf_bootstrap['openshift_provision_config_hierarchy'],
                jinja_vars = conf_bootstrap
            )
        )
        for item in conf_hierarchy[::-1]:
            self.load_cluster_vars(item)

        self.cluster_config['demo_dynamic_vars'] = {}
        self.cloud_provider_class = __import__(
            'openshift_' + self.cluster_config['demo_cloud_provider']
        )
        self.cloud_provider = getattr(
            self.cloud_provider_class,
            self.cloud_provider_class.inventory_class_name
        )(self)

    def load_vars_file(self, path):
        try:
            return yaml.load(
                open(self.openshift_provision_project_dir + '/' + path, 'r')
            )
        except Exception as e:
            raise Exception(
                'Unable to read vars file {}: {}'.format(path, e)
            )

    def load_cluster_vars(self, path):
        vardir = path + '/vars'
        for varfile in os.listdir(self.openshift_provision_project_dir + '/' + vardir):
            if not re.match(r'\w.*\.(ya?ml|json)$', varfile):
                continue
            varpath = vardir + '/' + varfile
            self.cluster_config.update(
                self.load_vars_file(varpath) or {}
            )

    def cluster_var(self, varname):
        """
        Return the value of a given variable.

        This method provides simplistic variable evaluation by the inventory
        to get a variable. This is needed to evaluated variables used to
        retrieve the inventory such as getting cloud provider information.
        """
        raw_value = self.cluster_config.get(varname, None)
        if isinstance(raw_value, str):
            return self.value_expand(raw_value)
        else:
            return raw_value

    def set_dynamic_cluster_var(self, varname, value):
        """
        Set the value of specified inventory variable.
        """
        self.cluster_config[varname] = value
        self.cluster_config['demo_dynamic_vars'][varname] = value

    def value_expand(self, value, depth=0, jinja_vars=None):
        if depth > 10:
            raise Exception("Variable expansion depth limit exceeded")
        elif isinstance(value, six.string_types) and '{{' in value:
            t = jinja2.Template(value)
            if not jinja_vars:
                jinja_vars = self.cluster_config
            return self.value_expand(
                t.render(jinja_vars),
                depth = depth + 1,
                jinja_vars = jinja_vars
            )
        else:
            return value

    def print_host_json(self, hostname):
        host = self.cloud_provider.get_host(hostname)
        if host:
            print(json.dumps(host, sort_keys=True, indent=2))
        else:
            print('{}')

    def print_host_list_json(self):
        hosts = {
            'all': {
                'vars': self.cluster_config
            },
            'controller': {
                'hosts': []
            },
            'OSEv3': {
                'children': ['etcd', 'nodes'],
                'hosts': []
            },
            'nodes': {
                'children': ['masters'],
                'hosts': []
            },
            'masters': {
                'hosts': []
            },
            'static-nodes': {
                'children': []
            },
            '_meta': {
                'hostvars': {}
            }
        }

        demo_openshift_node_groups = self.cluster_var('demo_openshift_node_groups')
        for group_name, node_group in demo_openshift_node_groups.items():
            if node_group.get('static_node_group', False) in [True, "true", "True", "yes"]:
                ansible_group = 'masters' if group_name == 'master' else group_name
                hosts['static-nodes']['children'].append(ansible_group)

        self.cloud_provider.populate_hosts(hosts)

        # Put etcd on masters if separate etcd nodes were not indicated
        if 'etcd' not in hosts:
            hosts['etcd'] = {
                'children': ['masters']
            }

        print(json.dumps(hosts, sort_keys=True, indent=2))

    def wait_for_hosts_running(self, timeout):
        self.cloud_provider.wait_for_hosts_running(timeout)

    def create_node_image(self):
        self.cloud_provider.create_node_image()

    def cleanup(self):
        self.cloud_provider.cleanup()

    def init(self):
        self.cloud_provider.init()

    def scaleup(self):
        self.cloud_provider.scaleup()
