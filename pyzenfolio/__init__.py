from __future__ import print_function, unicode_literals


__version__ = '0.9.1'
__author__ = 'Miroslav Shubernetskiy'

try:
    from .api import PyZenfolio  # noqa
    from .exceptions import APIError  # noqa
    from .helpers import search_sets_by_title  # noqa
except ImportError:
    pass
