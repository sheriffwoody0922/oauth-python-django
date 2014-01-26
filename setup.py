#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os
import re


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('oauth2_provider')


LONG_DESCRIPTION = open('README.rst').read()

setup(
    name="django-oauth-toolkit",
    version=version,
    description="OAuth2 goodies for Django",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='django oauth oauth2 oauthlib',
    author="Federico Frenguelli, Massimiliano Pippi",
    author_email='synasius@gmail.com, mpippi@gmail.com',
    url='https://github.com/evonove/django-oauth-toolkit',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    test_suite='runtests',
    install_requires=[
        'django>=1.4',
        'django-braces==1.2.2',
        'six==1.3.0',
        'oauthlib==0.6.1',
    ],
    zip_safe=False,
)
