from __future__ import unicode_literals, print_function
import six
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from .constants import DATETIME_FORMAT


class SSLAdapter(HTTPAdapter):
    """
    An HTTPS Transport Adapter that uses an arbitrary SSL version.
    https://lukasa.co.uk/2013/01/Choosing_SSL_Version_In_Requests/
    """

    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version
        super(SSLAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=self.ssl_version)


class AttrDict(dict):
    def __init__(self, data):
        super(AttrDict, self).__init__(data)
        self.convert(self, self.items())
        self.__dict__ = self

    def convert(self, root, items):
        for k, v in items:
            if isinstance(v, dict):
                root[k] = AttrDict(v)
            elif isinstance(v, (list, tuple)):
                self.convert(v, enumerate(v))


class ConvertToDateTime(object):
    """
    Finds all DateTime instances and converts to datetime objects.
    """

    def find_and_convert_dates(self, root, items):
        for k, v in items:
            if isinstance(v, dict):
                if '$type' in v and v['$type'] == 'DateTime':
                    root[k] = datetime.strptime(v['Value'], DATETIME_FORMAT)
                else:
                    self.find_and_convert_dates(v, v.items())
            elif isinstance(v, (list, tuple)):
                self.find_and_convert_dates(v, enumerate(v))

    def __call__(self, data):
        self.find_and_convert_dates(data, data.items())
        return data


convert_to_datetime = ConvertToDateTime()


def convert_from_datetime(value):
    if isinstance(value, datetime):
        return AttrDict({
            '$type': 'DateTime',
            'Value': value.strftime(DATETIME_FORMAT)
        })
    return value
