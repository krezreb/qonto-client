#!/bin/env python3

# -*- coding: utf-8 -*-

import setuptools
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setup(name='qonto_client',
    version='0.3',
    description='A python client for Qonto',
    long_description=long_description,
    long_description_content_type="text/markdown",      
    url='https://github.com/krezreb/qonto-client',
    author='krezreb',
    author_email='josephbeeson@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        'requests', 'ofxtools', 'schwifty', 'XlsxWriter'
    ],
    zip_safe=False)





