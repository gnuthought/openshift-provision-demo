#!/usr/bin/env python

from datetime import datetime
import googleapiclient.discovery
import googleapiclient.errors
import jinja2
import json
import logging
import os
import re
import requests
import sys
import time
import traceback
import weakref
import yaml

inventory_class_name = 'OpenShiftGCP'

class OpenShiftGCP:
    def __init__(self, ocpinv):
        self.ocpinv = weakref.ref(ocpinv)
        self.computeAPI = googleapiclient.discovery.build('compute', 'v1')
        self.dnsAPI = googleapiclient.discovery.build('dns', 'v1')
        self.set_dynamic_cloud_vars()

    def set_dynamic_cloud_vars(self):
        if not self.ocpinv().cluster_var('openshift_gcp_project'):
            self.set_openshift_gcp_project()
        if self.ocpinv().cluster_var('openshift_provision_use_cloud_dns'):
            self.set_cluster_domain_dns_servers()
        if not self.ocpinv().cluster_var('openshift_master_cluster_hostname'):
            self.set_master_cluster_hostname_with_loadbalancer_ip()
        if self.ocpinv().cluster_var('openshift_provision_wildcard_dns'):
            self.set_wildcard_dns_vars()

    def set_openshift_gcp_project(self):
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            self.set_openshift_gcp_project_from_google_creds()
        else:
            self.set_openshift_gcp_project_from_metadata()

    def set_openshift_gcp_project_from_google_creds(self):
        try:
            fh = open(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
            gcred = json.loads(fh.read())
            self.ocpinv().set_dynamic_cluster_var('openshift_gcp_project', gcred['project_id'])
        except:
            traceback.print_exec()
            raise Exception("Unable to determine openshift_gcp_project from GOOGLE_APPLICATION_CREDENTIALS")

    def set_openshift_gcp_project_from_metadata(self):
        try:
            r = requests.get(
                'http://metadata.google.internal/computeMetadata/v1/project/project-id',
                headers = { "Metadata-Flavor": "Google" }
            )
            r.raise_for_status()
            self.ocpinv().set_dynamic_cluster_var('openshift_gcp_project', r.text)
        except:
            traceback.print_exec()
            raise Exception("Unable to determine openshift_gcp_project from GOOGLE_APPLICATION_CREDENTIALS")

    def set_cluster_domain_dns_servers(self):
        """
        Set openshift_provision_cluster_domain_dns_servers based on dynamically
        determined name server list.
        """
        cluster_zone = self.dnsAPI.managedZones().get(
            managedZone = self.ocpinv().cluster_var('openshift_provision_gcp_dns_zone_name'),
            project = self.ocpinv().cluster_var('openshift_gcp_project')
        ).execute()
        self.ocpinv().set_dynamic_cluster_var(
            'openshift_provision_cluster_domain_dns_servers',
            cluster_zone['nameServers']
        )

    def set_master_cluster_hostname_with_loadbalancer_ip(self):
        gcp_prefix = self.ocpinv().cluster_var('openshift_gcp_prefix')
        resp = self.computeAPI.forwardingRules().list(
            filter = '(name="{}master")'.format(gcp_prefix),
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            region = self.ocpinv().cluster_var('openshift_gcp_region')
        ).execute()
        for forwarding_rule in resp.get('items', []):
            self.ocpinv().set_dynamic_cluster_var(
                'openshift_master_cluster_hostname',
                forwarding_rule['IPAddress']
            )
            return

    def set_wildcard_dns_vars(self):
        wildcard_dns = self.ocpinv().cluster_var('openshift_provision_wildcard_dns')
        master_ip, router_ip = self.get_master_and_router_ip()
        if master_ip:
            self.ocpinv().set_dynamic_cluster_var(
                'openshift_master_cluster_public_hostname',
                "master.{}.{}".format(
                    master_ip,
                    wildcard_dns
                )
            )
        if router_ip:
            self.ocpinv().set_dynamic_cluster_var(
                'openshift_master_default_subdomain',
                "{}.{}".format(
                    router_ip,
                    wildcard_dns
                )
            )

    def get_master_and_router_ip(self):
        gcp_prefix = self.ocpinv().cluster_var('openshift_gcp_prefix')
        if self.ocpinv().cluster_var('openshift_provision_shared_public_load_balancer'):
            ip = self.get_globaladdress_ip(gcp_prefix + 'public')
            return ip, ip
        else:
            master_ip = self.get_globaladdress_ip(gcp_prefix + 'master')
            router_ip = self.get_globaladdress_ip(gcp_prefix + 'router')
            return master_ip, router_ip

    def get_globaladdress_ip(self, name):
        resp = self.computeAPI.globalAddresses().list(
            filter = 'name="{}"'.format(name),
            project = self.ocpinv().cluster_var('openshift_gcp_project')
        ).execute()
        for address in resp.get('items', []):
            return address['address']

    def instance_fqdn(self, instance):
        return '%s.c.%s.internal' % (
            instance['name'],
            self.ocpinv().cluster_var('openshift_gcp_project')
        )

    def instance_belongs_to_cluster(self, instance):
        return(
            self.ocpinv().cluster_name == instance.get('labels',{}).get('openshift-cluster','')
        )

    def get_cluster_zones(self):
        """
        Return list of zones configured for the cluster or list of all zones
        for the region.
        """

        config_zones = self.ocpinv().cluster_var('openshift_provision_gcp_zones')
        if config_zones:
            return config_zones

        if not self.ocpinv().cluster_var('openshift_gcp_multizone'):
            gcp_zone = self.ocpinv().cluster_var('openshift_gcp_zone')
            self.ocpinv().cluster_config['openshift_provision_gcp_zones'] = [gcp_zone]
            return [gcp_zone]

        region = self.computeAPI.regions().get(
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            region = self.ocpinv().cluster_var('openshift_gcp_region')
        ).execute()
        gcp_zones = [
            zone_uri.rsplit('/',1)[-1] for zone_uri in region['zones']
        ]
        self.ocpinv().cluster_config['openshift_provision_gcp_zones'] = gcp_zones
        return gcp_zones

    def get_instance_in_zone(self, hostname, zone):
        try:
            instance = self.computeAPI.instances().get(
                instance = hostname.split('.')[0],
                project = self.ocpinv().cluster_var('openshift_gcp_project'),
                zone = zone
            ).execute()
        except googleapiclient.errors.HttpError:
            return None
        if self.instance_belongs_to_cluster(instance):
            return instance
        # False means found instance and instance does not belong to this cluster
        return False

    def get_instance(self, hostname):
        for zone in self.get_cluster_zones():
            instance = self.get_instance_in_zone(hostname, zone)
            if instance != None:
                return instance
        return None

    def get_cluster_instances(self):
        for zone in self.get_cluster_zones():
            for instance in self.get_cluster_instances_in_zone(zone):
                yield instance

    def get_cluster_instances_in_zone(self, zone):
        for instance in self.get_instances_in_zone(zone):
            if( self.instance_belongs_to_cluster(instance)
            and self.ansible_group_filter(instance) ):
                # FIXME - Should have a mechanism to exclude dynamic/autoscaling instances
                yield instance

    def get_instances_in_zone(self, zone):
        req = self.computeAPI.instances().list(
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            zone = zone
        )
        while req:
            resp = req.execute()
            for instance in resp.get('items', []):
                yield instance
            req = self.computeAPI.instances().list_next(
                previous_request = req,
                previous_response = resp
            )

    def instance_ansible_host_groups(self, instance):
        groups = []
        for item in instance['metadata']['items']:
            if( item['key'].startswith('ansible-host-group-')
            and item['value'] == 'true'):
                groups.append(item['key'][19:])
        if groups:
            return groups
        else:
            # Did not find any ansible-host-group-* metadata, default to nodes
            return ['nodes']

    def instance_openshift_node_group_name(self, instance):
        name = instance['labels'].get('openshift-node-group-name', 'compute')
        # Drop useless "node-config-" prefix if present
        if name.startswith('node-config-'):
            return name[12:]
        return name

    def instance_openshift_node_labels(self, instance):
        node_labels = {
            'failure-domain.beta.kubernetes.io/region':
                self.ocpinv().cluster_var('openshift_gcp_region'),
            'failure-domain.beta.kubernetes.io/zone':
                instance['zone'].rsplit('/',1)[1]
        }

        node_group_name = self.instance_openshift_node_group_name(instance)
        node_group_labels = self.ocpinv().cluster_config \
            .get('openshift_provision_node_groups', {}) \
            .get(node_group_name, {}) \
            .get('labels', {'node-role.kubernetes.io/'+node_group_name: 'true' })
        node_labels.update(node_group_labels)
        return node_labels

    def instance_ansible_host_ip(self, instance):
        primary_network_interface = instance['networkInterfaces'][0]
        if os.environ.get('GCP_ANSIBLE_INVENTORY_USE_NAT_IP', 'false') == 'true':
            return primary_network_interface['accessConfigs'][0]['natIP']
        else:
            return primary_network_interface['networkIP']

    def instance_add_host_storage_devices(self, instance, hostvars):
        glusterfs_devices = []
        for disk in instance['disks']:
            device =  '/dev/disk/by-id/google-' + disk['deviceName']
            if re.match(r'docker(-?vg)?$', disk['deviceName']):
                hostvars['container_runtime_docker_storage_setup_device'] = device
            elif disk['deviceName'].startswith('glusterfs-'):
                glusterfs_devices.append(device)
        if len(glusterfs_devices) > 0:
            hostvars['glusterfs_devices'] = glusterfs_devices

    def instance_add_ansible_vars(self, instance, hostvars):
        for item in instance['metadata']['items']:
            if item['key'].startswith('ansible-var-'):
                try:
                    value = json.loads(item['value'])
                except:
                    value = item['value']
                hostvars[item['key'][12:]] = value

        return hostvars

    def instance_host_vars(self, instance):
        hostvars = {
            'ansible_host': self.instance_ansible_host_ip(instance)
        }
        self.instance_add_ansible_vars(instance, hostvars)

        if instance.get('labels',{}).get('openshift-cluster-controller', 'false') != 'true':
            hostvars['openshift_node_group_name'] = 'node-config-' + self.instance_openshift_node_group_name(instance)
            hostvars['openshift_node_labels'] = self.instance_openshift_node_labels(instance)
            self.instance_add_host_storage_devices(instance, hostvars)

        self.instance_add_ansible_vars(instance, hostvars)
        return hostvars

    def ansible_group_filter(self, instance):
        if 'ANSIBLE_GROUP_FILTER' not in os.environ:
            return True
        for item in instance['metadata']['items']:
            if( item['key'] == 'ansible-host-group-' + os.environ['ANSIBLE_GROUP_FILTER']
            and item['value'] == 'true' ):
                return True
        return False

    def openshift_role_filter(self, hostvars):
        if 'OPENSHIFT_ROLE_FILTER' not in os.environ:
            return True
        for role in os.environ['OPENSHIFT_ROLE_FILTER'].split(','):
            kuberole = 'node-role.kubernetes.io/' + role
            if kuberole in hostvars.get('openshift_node_labels', {}):
                return True
        return False

    def get_host(self, hostname):
        instance = self.get_instance(hostname)

        if not instance or instance['status'] != 'RUNNING':
            return
        else:
            return self.instance_host_vars(instance)

    def populate_hosts_with_instances(self, hosts):
        for instance in self.get_cluster_instances():
            # Skip instances that are not running
            if instance['status'] != 'RUNNING':
                continue
            hostvars = self.instance_host_vars(instance)

            if not self.openshift_role_filter(hostvars):
                continue

            fqdn = self.instance_fqdn(instance)
            hosts['_meta']['hostvars'][fqdn] = hostvars

            for group in self.instance_ansible_host_groups(instance):
                if group in hosts:
                    hosts[group]['hosts'].append(fqdn)
                else:
                    hosts[group] = {
                        'hosts': [fqdn]
                    }

    def populate_hosts(self, hosts):
        self.populate_hosts_with_instances(hosts)

    def wait_for_hosts_running(self, timeout):
        start_time = time.time()
        all_ready = False
        instance_name = ''
        instance_status = ''
        while timeout > time.time() - start_time:
            try:
                for instance in self.get_cluster_instances():
                    instance_name = instance['name']
                    instance_status = instance['status']
                    if instance['status'] != 'RUNNING':
                        raise Exception(
                            "Instance %s not status RUNNING" % (instance_name)
                        )
                all_ready = True
            except:
                pass
            if all_ready:
                break
            logging.info("Waiting for all instances to be RUNNING")
            time.sleep(2)
        if not all_ready:
            raise Exception("Instance %s found with status %s" % (instance_name, instance_status))

    def stop_instance(self, instance):
        instance_zone = instance['zone'].rsplit('/', 1)[1]

        self.computeAPI.instances().stop(
            instance = instance['name'],
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            zone = instance_zone
        ).execute()

        while instance['status'] != 'TERMINATED':
            time.sleep(5)
            instance = self.get_instance_in_zone(instance['name'], instance_zone)

    def delete_instance(self, instance):
        instance_zone = instance['zone'].rsplit('/', 1)[1]

        self.computeAPI.instances().delete(
            instance = instance['name'],
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            zone = instance_zone
        ).execute()

        while instance:
            time.sleep(5)
            instance = self.get_instance_in_zone(instance['name'], instance_zone)

    def create_node_image(self):
        image_instance_name = self.ocpinv().cluster_var('openshift_gcp_prefix') + 'image'
        image_name = self.ocpinv().cluster_var('openshift_gcp_prefix') + 'node-' + datetime.now().strftime('%Y%m%d%H%M%S')
        instance = self.get_instance(image_instance_name)
        if not instance:
            raise Exception("Unable to find cluster image instance.")
        self.stop_instance(instance)
        self.computeAPI.images().insert(
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            body = {
                "name": image_name,
                "family": self.ocpinv().cluster_var('openshift_provision_gcp_node_image_family'),
                "labels": {
                    "openshift-cluster": self.ocpinv().cluster_name
                },
                "sourceDisk": instance['disks'][0]['source']
            }
        ).execute()
        while True:
            image = self.computeAPI.images().get(
                image = image_name,
                project = self.ocpinv().cluster_var('openshift_gcp_project'),
            ).execute()
            if image['status'] == 'READY':
                break
        self.delete_instance(instance)

    def scaleup(self):
        node_groups = self.ocpinv().cluster_config.get('openshift_provision_node_groups', {})
        for node_group_name, node_group in node_groups.items():
            if node_group.get('static_node_group', False):
                continue
            minimum_instance_count = node_group.get(
                'minimum_instance_count',
                node_group.get('instance_count', 0)
            )
            gcp_zones = self.get_cluster_zones()
            zone_count = len(gcp_zones)
            for i, zone in enumerate(gcp_zones):
                minimum_target_size = int(
                    (minimum_instance_count + zone_count - i - 1) / zone_count
                )

                instance_group_name = (
                    self.ocpinv().cluster_var('openshift_gcp_prefix') +
                    node_group_name + zone[-2:]
                )

                self.scaleup_managed_instance_group(
                    instance_group_name,
                    zone,
                    minimum_target_size
                )

    def scaleup_managed_instance_group(
        self,
        instance_group_name,
        zone,
        minimum_target_size
    ):
        if minimum_target_size < 1:
            return

        instance_group_manager = self.computeAPI.instanceGroupManagers().get(
            project = self.ocpinv().cluster_var('openshift_gcp_project'),
            zone = zone,
            instanceGroupManager = instance_group_name
        ).execute()

        if instance_group_manager['targetSize'] < minimum_target_size:
            logging.info("Scaling up %s to %d" % (instance_group_name, minimum_target_size))
            instance_group_manager = self.computeAPI.instanceGroupManagers().resize(
                project = self.ocpinv().cluster_var('openshift_gcp_project'),
                zone = zone,
                instanceGroupManager = instance_group_name,
                size = minimum_target_size
            ).execute()
            return True
