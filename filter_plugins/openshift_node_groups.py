def provision_to_openshift_node_groups(source, delim='='):
    ''' Returns definition of openshift_node_groups from openshift_provision_node_groups '''
    openshift_node_groups = []
    return [ {
        'name': 'node-config-' + k,
        'labels': [ '%s=%s' % (k, v) for k, v in v['labels'].items() ],
        'edits': []
    } for k, v in source.items()]

class FilterModule(object):
    ''' OpenShift Filters for selector strings '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns filters provided by this class '''
        return {
            'provision_to_openshift_node_groups': provision_to_openshift_node_groups
        }
