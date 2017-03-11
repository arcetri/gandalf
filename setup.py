#!/usr/bin/env python

import os
import pip
from setuptools import setup


setup(
    name='gandalf',
    version='0.1.0',
    description='Configuration files rendering script',
    author='Sergei Fomin',
    author_email='sergio-dna@yandex.ru',
    py_modules=['gandalf'],
    install_requires=['tinydb', 'mako', 'pyyaml'],
    entry_points = {
        'console_scripts': [
            'gandalf = gandalf:main'
        ],
    }
)
