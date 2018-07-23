import copy

def dict_to_named_list(source, nameattr='name'):
    ''' Returns a list from the source dict '''
    named_list = []
    for k, v in source.items():
        c = copy.deepcopy(v)
        c[nameattr] = k
        named_list.append(c)
    return named_list

class FilterModule(object):
    ''' OpenShift Filter for manipulating dicts to lists '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns filters provided by this class '''
        return {
            'dict_to_named_list': dict_to_named_list
        }
