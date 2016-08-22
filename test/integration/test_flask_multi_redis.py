#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Integration tests for Flask-Multi-Redis."""

import flask
from flask_multi_redis import Aggregator
from flask_multi_redis import FlaskMultiRedis
import pytest
from redis import StrictRedis


@pytest.fixture
def app():
    return flask.Flask(__name__)


@pytest.fixture
def loadbalanced(app):
    return FlaskMultiRedis(app)


@pytest.fixture
def aggregated(app):
    return FlaskMultiRedis(app, strategy='aggregate')


@pytest.fixture
def app_custom_default(app):
    app.config['REDIS_DEFAULT_PORT'] = 16379
    app.config['REDIS_DEFAULT_DB'] = 9
    app.config['REDIS_DEFAULT_PASSWORD'] = 'password'
    app.config['REDIS_DEFAULT_SOCKET_TIMEOUT'] = 2
    return app


@pytest.fixture
def app_custom_default_ssl(app):
    app.config['REDIS_DEFAULT_SSL'] = {
                                          'ssl_keyfile': 'ssl/rediskey.pem',
                                          'ssl_certfile': 'ssl/rediscert.pem',
                                          'ssl_ca_certs': 'ssl/rediscert.pem',
                                          'ssl_cert_reqs': 'required'
                                      }
    return app


@pytest.fixture
def app_custom_node(app):
    ssl = {
              'ssl_keyfile': 'ssl/rediskey.pem',
              'ssl_certfile': 'ssl/rediscert.pem',
              'ssl_ca_certs': 'ssl/rediscert.pem',
              'ssl_cert_reqs': 'required'
          }
    app.config['REDIS_NODES'] = [{
                                     'host': 'localhost',
                                     'port': 16379,
                                     'db': 9,
                                     'password': 'password',
                                     'timeout': 2,
                                     'ssl': ssl
                                }]
    return app


def test_constructor(loadbalanced):
    """Test that a constructor with app instance will initialize the
    connection."""
    assert loadbalanced._redis_client is not None
    assert hasattr(loadbalanced._redis_client, 'connection_pool')
    assert hasattr(loadbalanced._app, 'extensions')
    assert 'redis' in loadbalanced._app.extensions
    assert loadbalanced._app.extensions['redis'] is loadbalanced


def test_aggregator_strategy(aggregated):
    """Test that a constructor with aggregate strategy will initialize
    the connection."""
    assert aggregated._redis_client is not None
    assert hasattr(aggregated._redis_client, 'connection_pool')
    assert hasattr(aggregated._app, 'extensions')
    assert 'redis' in aggregated._app.extensions
    assert aggregated._app.extensions['redis'] == aggregated


def test_extension_registration_if_app_has_no_extensions(app):
    """Test that the constructor is able to register FlaskMultiRedis
    as an extension even if app has no extensions attribute."""
    delattr(app, 'extensions')
    redis = FlaskMultiRedis(app)
    assert hasattr(app, 'extensions')
    assert 'redis' in app.extensions
    assert app.extensions['redis'] == redis


def test_init_app(app):
    """Test that a constructor without app instance will not initialize the
    connection.

    After FlaskMultiRedis.init_app(app) is called, the connection will be
    initialized."""
    redis = FlaskMultiRedis()
    assert redis._app is None
    assert len(redis._redis_nodes) == 0
    redis.init_app(app)
    assert redis._app is app
    assert len(redis._redis_nodes) == 1
    assert hasattr(redis._redis_client, 'connection_pool')


def test_custom_prefix(app):
    """Test that config prefixes enable distinct connections."""
    app.config['DBA_NODES'] = [{'host': 'localhost', 'db': 1}]
    app.config['DBB_NODES'] = [{'host': 'localhost', 'db': 2}]
    redis_a = FlaskMultiRedis(app, config_prefix='DBA')
    redis_b = FlaskMultiRedis(app, config_prefix='DBB')
    assert redis_a.connection_pool.connection_kwargs['db'] == 1
    assert redis_b.connection_pool.connection_kwargs['db'] == 2


def test_strict_parameter(app):
    """Test that initializing with the strict parameter set to True will use
    StrictRedis, and that False will keep using the old Redis class."""

    redis = FlaskMultiRedis(app, strict=True)
    assert redis._redis_client is not None
    assert type(redis._redis_client).__name__ == 'StrictRedis'

    redis = FlaskMultiRedis(app, strict=False)
    assert redis._redis_client is not None
    assert type(redis._redis_client).__name__ == 'Redis'


def test_custom_provider(app):
    """Test that FlaskMultiRedis can be instructed to use a different Redis client,
    like StrictRedis."""
    class FakeProvider(object):

        def __init__(self, **kwargs):
            pass

    redis = FlaskMultiRedis.from_custom_provider(FakeProvider)
    assert isinstance(redis, FlaskMultiRedis)
    assert redis._redis_client is None
    redis.init_app(app)
    assert redis._redis_client is not None
    assert isinstance(redis._redis_client, FakeProvider)


def test_custom_provider_with_app(app):
    """Test that FlaskMultiRedis can be instructed to use a different Redis client,
    using an already existing Flask app."""
    class FakeProvider(object):

        def __init__(self, **kwargs):
            pass

    redis = FlaskMultiRedis.from_custom_provider(FakeProvider, app=app)
    assert isinstance(redis, FlaskMultiRedis)
    assert redis._redis_client is not None
    assert isinstance(redis._redis_client, FakeProvider)


def test_custom_provider_is_none(app):
    """Test that FlaskMultiRedis cannot be instructed to use a Redis Client
    wich is None."""
    with pytest.raises(AssertionError) as excinfo:
        FlaskMultiRedis.from_custom_provider(None)
        assert excinfo.value == 'your custom provider is None, come on'


def test_custom_default_config(app_custom_default):
    """Test that we can pass a custom default configuration."""

    redis = FlaskMultiRedis(app_custom_default)
    assert redis.connection_pool.connection_kwargs['port'] == 16379
    assert redis.connection_pool.connection_kwargs['db'] == 9
    assert redis.connection_pool.connection_kwargs['password'] == 'password'
    assert redis.connection_pool.connection_kwargs['socket_timeout'] == 2


def test_custom_default_ssl(app_custom_default_ssl):
    """Test that we can pass a custom default ssl configuration."""

    redis = FlaskMultiRedis(app_custom_default_ssl)
    kwargs = redis.connection_pool.connection_kwargs
    assert kwargs['ssl_keyfile'] == 'ssl/rediskey.pem'
    assert kwargs['ssl_certfile'] == 'ssl/rediscert.pem'
    assert kwargs['ssl_ca_certs'] == 'ssl/rediscert.pem'
    assert kwargs['ssl_cert_reqs'] == 'required'


def test_custom_node(app_custom_node):
    """Test that we can pass a custom node configuration."""

    redis = FlaskMultiRedis(app_custom_node)
    kwargs = redis.connection_pool.connection_kwargs
    assert kwargs['port'] == 16379
    assert kwargs['db'] == 9
    assert kwargs['password'] == 'password'
    assert kwargs['socket_timeout'] == 2
    assert kwargs['ssl_keyfile'] == 'ssl/rediskey.pem'
    assert kwargs['ssl_certfile'] == 'ssl/rediscert.pem'
    assert kwargs['ssl_ca_certs'] == 'ssl/rediscert.pem'
    assert kwargs['ssl_cert_reqs'] == 'required'


def test_attributes_transmission_from_loadbalanced_node(loadbalanced):
    """Test that attributes from loadbalanced nodes are
    available directly from FlaskMultiRedis object."""

    node = loadbalanced._redis_nodes[0]
    assert loadbalanced.connection_pool is node.connection_pool


def test_attributes_transmission_from_aggregated_node(aggregated):
    """Test that attributes from aggregated nodes are
    available directly from FlaskMultiRedis object."""

    node = aggregated._aggregator._redis_nodes[0]
    assert aggregated.connection_pool is node.connection_pool


def test_methods_transmission_from_aggregator(aggregated):
    """Test that methods from aggregator are available
    directly from FlaskMultiRedis object (aggregate)."""

    assert isinstance(aggregated.keys.__self__, Aggregator)


def test_methods_transmission_from_redis(loadbalanced):
    """Test that methods from redis are available
    direcly from FlaskMultiRedis object (loadbalancing)."""

    assert isinstance(loadbalanced.keys.__self__, StrictRedis)
