#!/bin/env/python

from os import environ
from subprocess import call

commands = [['python-codacy-coverage', '-r', 'coverage.xml'],
            ['/usr/bin/env', 'codecov', '-e', 'TOXENV']]

if __name__ == '__main__':
    if 'TRAVIS' in environ:
        for command in commands:
            rc = call(command)
