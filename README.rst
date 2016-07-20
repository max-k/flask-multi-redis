Flask-Multi-Redis
=================

.. image:: https://api.travis-ci.org/max-k/flask-multi-redis.svg?branch=master
   :target: https://travis-ci.org/max-k/flask-multi-redis
   :alt: Test Suite

.. image:: https://codecov.io/gh/max-k/flask-multi-redis/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/max-k/flask-multi-redis
   :alt: Coverage Status

.. image:: https://landscape.io/github/max-k/flask-multi-redis/master/landscape.svg?style=flat
   :target: https://landscape.io/github/max-k/flask-multi-redis
   :alt: Code Health

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
