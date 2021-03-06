Flask-Multi-Redis
=================

*CI Status*

.. image:: https://api.travis-ci.org/max-k/flask-multi-redis.svg?branch=master
   :target: https://travis-ci.org/max-k/flask-multi-redis
   :alt: Travis CI Status

.. image:: https://codecov.io/gh/max-k/flask-multi-redis/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/max-k/flask-multi-redis
   :alt: Codecov Coverage Status

.. image:: https://coveralls.io/repos/github/max-k/flask-multi-redis/badge.svg
   :target: https://coveralls.io/github/max-k/flask-multi-redis
   :alt: Coveralls Coverage Status

.. image:: https://api.codacy.com/project/badge/Coverage/aac58b911e074237ab13a029e8a433eb
   :target: https://www.codacy.com/app/max-k/flask-multi-redis/dashboard
   :alt: Codacy Coverage Status

.. image:: https://api.codacy.com/project/badge/Grade/aac58b911e074237ab13a029e8a433eb
   :target: https://www.codacy.com/app/max-k/flask-multi-redis/dashboard
   :alt: Codacy Code Grade

.. image:: https://landscape.io/github/max-k/flask-multi-redis/master/landscape.svg?style=flat
   :target: https://landscape.io/github/max-k/flask-multi-redis
   :alt: Landscape Code Health

.. image:: https://codeclimate.com/github/max-k/flask-multi-redis/badges/gpa.svg
   :target: https://codeclimate.com/github/max-k/flask-multi-redis
   :alt: Code Climate

.. image:: https://codeclimate.com/github/max-k/flask-multi-redis/badges/coverage.svg
   :target: https://codeclimate.com/github/max-k/flask-multi-redis/coverage
   :alt: Code Climate Coverage

*PyPI Status*

.. image:: https://img.shields.io/pypi/v/Flask-Multi-Redis.svg
   :target: https://pypi.python.org/pypi/Flask-Multi-Redis
   :alt: Pypi Version

.. image:: https://img.shields.io/pypi/status/Flask-Multi-Redis.svg
   :target: https://pypi.python.org/pypi/Flask-Multi-Redis
   :alt: Pypi Status

.. image:: https://img.shields.io/pypi/implementation/Flask-Multi-Redis.svg
   :target: https://pypi.python.org/pypi/Flask-Multi-Redis
   :alt: Python Implementation

.. image:: https://img.shields.io/pypi/pyversions/Flask-Multi-Redis.svg
   :target: https://pypi.python.org/pypi/Flask-Multi-Redis
   :alt: Python Versions

.. image:: https://img.shields.io/badge/license-aGPLv3+%20License-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0.html
   :alt: License aGPLv3+

----

Adds Redis support to Flask with fail-over or aggregation capabilities.

Mostly inspired by these projects :

 - Flask-Redis - https://github.com/underyx/flask-redis
 - Beholder - https://github.com/druidops/beholder

Built on top of redis-py_.

Contributors
------------

 - Thomas Sarboni - @maxk69 - https://github.com/max-k

Description
-----------

Flask-Multi-Redis allows you to easily access multiple Redis_ servers from Flask_ applications.
It supports SSL connections and password authentication.
It's not intended to implement all Redis commands but gives you the hability to make multi-threaded
parallel queries to multiple Redis servers without the need to deploy a Redis cluster.

Installation
------------

.. code-block:: bash

    pip install flask-multi-redis

Configuration
-------------

Enable Flask-Multi-Redis in your application :

.. code-block:: python

    from flask import Flask
    from flask.ext.redis import FlaskRedis

    app = Flask(__name__)
    redis_store = FlaskRedis(app)

Flask-Multi-Redis provide a simple flexible configuration handling.
It reads its configuration from your Flask app.config dictionnary.

Default configuration for all servers :

.. code-block:: python

    app.config['REDIS_DEFAULT_PORT'] = 6379
    app.config['REDIS_DEFAULT_DB'] = 0
    app.config['REDIS_DEFAULT_PASSWORD'] = None
    app.config['REDIS_DEFAULT_SOCKET_TIMEOUT'] = 5
    app.config['REDIS_DEFAULT_SSL'] = None

Usage
-----

FlaskMultiRedis proxies attribute access to an underlying Redis connection.
So treat it as if it were a regular Redis instance.

.. code-block:: python

    @app.route('/')
    def index():
        return redis_store.get('potato', 'Not Set')

Protip: The redis-py package currently holds the 'redis' namespace,
so if you are looking to make use of it, your Redis object shouldn't be named 'redis'.

For detailed instructions regarding the usage of the client, check the redis-py documentation.

Advanced features, such as Lua scripting, pipelines and callbacks are detailed within the projects README.

Contribute
----------

.. _Redis: http://redis.io/
.. _Flask: http://flask.pocoo.org/
.. _redis-py: https://github.com/andymccurdy/redis-py
