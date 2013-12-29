from __future__ import unicode_literals, print_function
import os
from setuptools import setup
from pyzenfolio import __version__, __author__


def get_packages(package):
    return [str(dirpath)
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


def read(fname):
    return open(fname, 'rb').read().decode('utf-8')


setup(
    name="pyzenfolio",
    version=__version__,
    author=__author__,
    author_email="miroslav@miki725.com",
    description=("Light-weight Zenfolio API Python wrapper."),
    long_description=read('README.rst') + read('LICENSE.rst'),
    license="MIT",
    keywords="zenfolio",
    url="https://github.com/miki725/pyzenfolio",
    packages=get_packages('pyzenfolio'),
    install_requires=[
        'requests',
        'six',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python',
    ]
)
