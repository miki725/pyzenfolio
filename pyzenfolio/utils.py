from __future__ import print_function, unicode_literals
from datetime import datetime

from .constants import DATETIME_FORMAT


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
