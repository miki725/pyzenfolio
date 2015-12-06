from __future__ import print_function, unicode_literals

import six


class APIError(Exception):
    pass


class ConfigError(APIError):
    pass


@six.python_2_unicode_compatible
class ZenfolioError(APIError):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return '{} - {}'.format(self.code, self.message)


@six.python_2_unicode_compatible
class HTTPError(APIError):
    def __init__(self, url, status_code, headers, content):
        self.url = url
        self.status_code = status_code
        self.headers = headers
        self.content = content

    def __str__(self):
        return '{} - {}'.format(self.url, self.status_code)
