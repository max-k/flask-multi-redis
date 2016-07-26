#!/bin/env/python

from os import environ
from subprocess import call

commands = ['python-codacy-coverage -r coverage.xml',
            'codecov -e TOXENV']

if __name__ == '__main__':
    if 'TRAVIS' in environ:
        rc = call('coveralls')
        raise SystemExit(rc)
