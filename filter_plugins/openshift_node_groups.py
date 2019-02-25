'''
Ansible filter demo_to_openshift_node_groups

This filter converts from variable format of demo_openshift_node_groups to
openshift_node_groups expected format.
'''

def demo_to_openshift_node_groups(source):
    ''' Returns definition of openshift_node_groups from demo_openshift_node_groups '''
    return [{
        'name': 'node-config-' + node_group_name,
        'labels': [ '%s=%s' % (k, v) for k, v in node_group['labels'].items() ],
        'edits': []
    } for node_group_name, node_group in source.items()]

class FilterModule(object):
    ''' OpenShift Filters for selector strings '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns filters provided by this class '''
        return {
            'demo_to_openshift_node_groups': demo_to_openshift_node_groups
        }
