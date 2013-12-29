from __future__ import unicode_literals, print_function


class APIError(Exception):
    pass


class ConfigError(APIError):
    pass


class ZenfolioError(APIError):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class HTTPError(APIError):
    def __init__(self, url, status_code, headers, content):
        self.url = url
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.message = 'HTTP Error: {0} - {1}'.format(status_code, url)
