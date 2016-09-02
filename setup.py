#!/usr/bin/env python3

"""FlaskMultiRedis deployment configuration."""

import io

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with io.open('README.rst', encoding='utf-8') as f:
    README = f.read()
with io.open('HISTORY.rst', encoding='utf-8') as f:
    HISTORY = f.read()

with io.open('requirements.txt', encoding='utf-8') as f:
    INSTALL_REQS = f.read().splitlines()
with io.open('test-requirements.txt', encoding='utf-8') as f:
    TEST_REQS = f.read().splitlines()

DESC = "MultiThreaded MultiServers Redis Extension for Flask Applications"
LICENSE = "GNU Affero General Public License v3 or later (AGPLv3+)"

setup(
    name='Flask-Multi-Redis',
    version='0.1.3',
    url='https://github.com/max-k/flask-multi-redis',
    author='Thomas Sarboni',
    author_email='max-k@post.com',
    maintainer='Thomas Sarboni',
    maintainer_email='max-k@post.com',
    download_url='https://github.com/max-k/flask-multi-redis/releases',
    description=DESC,
    long_description=README + '\n\n' + HISTORY,
    packages=['flask_multi_redis'],
    zip_safe=False,
    setup_requires=['pytest-runner>=2.0,<3dev'],
    install_requires=INSTALL_REQS,
    tests_require=TEST_REQS,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ' + LICENSE,
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
