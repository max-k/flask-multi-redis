#!/usr/bin/env python3
import io

from setuptools import setup

with io.open('README.rst', encoding='utf-8') as f:
    README = f.read()
with io.open('HISTORY.rst', encoding='utf-8') as f:
    HISTORY = f.read()


setup(
    name='Flask-Multi-Redis',
    version='0.0.1',
    url='https://github.com/max-k/flask-multi-redis',
    author='Thomas Sarboni',
    author_email='max-k@post.com',
    maintainer='Thomas Sarboni',
    maintainer_email='max-k@post.com',
    download_url='https://github.com/max-k/flask-multi-redis/releases',
    description='MultiThreaded and MultiServers Redis Extension for Flask Applications',
    long_description=README + '\n\n' + HISTORY,
    packages=['flask_multi_redis'],
    package_data={'': ['LICENSE']},
    zip_safe=False,
    install_requires=[
        'Flask>=0.9',
        'redis>=2.6.8',
        'more-itertools>=2.1'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
