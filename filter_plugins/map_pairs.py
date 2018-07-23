def map_from_pairs(source, delim='='):
    ''' Returns a dict given the source and delim delimited '''
    if source == '':
        return dict()
    return dict(item.split(delim) for item in source.split(","))

def map_to_pairs(source, delim='='):
    ''' Returns a string of key/value pairs join by delim from dict '''
    return ',',join(k + delim + v for k, v in source.items())

class FilterModule(object):
    ''' OpenShift Filters for selector strings '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns filters provided by this class '''
        return {
            'map_from_pairs': map_from_pairs,
            'map_to_pairs': map_to_pairs
        }
