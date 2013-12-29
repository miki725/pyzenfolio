from __future__ import unicode_literals, print_function

__version__ = 0.9
__author__ = 'Miroslav Shubernetskiy'

try:
    from .api import PyZenfolio
    from .exceptions import APIError
    from .helpers import search_sets_by_title
except ImportError:
    pass
