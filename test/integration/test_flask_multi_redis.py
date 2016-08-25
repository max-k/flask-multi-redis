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


@pytest.fixture
def fake_node():
    class Node(object):
        def __init__(self, name):
            self.config = {'socket_timeout': 2}
            self.name = name

        def get(self, pattern):
            return self.name

        def ttl(self, pattern):
            if int(self.name[-1]) == 3:
                return None
            return int(self.name[-1])

        def keys(self, pattern):
            if int(self.name[-1]) == 3:
                return [self.name, pattern]
            return [pattern]

        def set(self, key, pattern):
            setattr(self, key, pattern)

        def delete(self, pattern):
            delattr(self, 'name')
    return Node


@pytest.fixture
def mocked_loadbalanced(loadbalanced, fake_node):
    loadbalanced._redis_nodes = [
                                    fake_node('node1'),
                                    fake_node('node2'),
                                    fake_node('node3')
                                ]
    return loadbalanced


@pytest.fixture
def mocked_aggregated(aggregated, fake_node):
    aggregated._aggregator._redis_nodes = [
                                              fake_node('node1'),
                                              fake_node('node2'),
                                              fake_node('node3')
                                          ]
    return aggregated


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


def test_attributes_transmission_if_aggregated_has_no_host(aggregated):
    """Test that attributes transmission return None if Aggregator
    has an empty node list."""
    aggregated._aggregator._redis_nodes = []
    assert aggregated._redis_client is None


def test_methods_transmission_from_redis(loadbalanced):
    """Test that methods from redis are available
    direcly from FlaskMultiRedis object (loadbalancing)."""

    assert isinstance(loadbalanced.keys.__self__, StrictRedis)


def test_methods_transmission_from_aggregator(aggregated):
    """Test that methods from aggregator are available
    directly from FlaskMultiRedis object (aggregate)."""

    assert isinstance(aggregated.keys.__self__, Aggregator)


def test_transmission_of_not_implemented_method(aggregated):
    """Test that trying to access a not implemented method
    will properly raise an exception."""

    with pytest.raises(NotImplementedError) as e:
        aggregated.mget

    message = 'NotImplementedError: mget is not implemented yet.'
    message += ' Feel free to contribute.'
    assert ' '.join(str(e).split(' ')[1:]) == message


def test_task_runner(mocked_aggregated):
    """Test task runner in nominal operations."""

    def task(node, pattern, aggregator):
        if node.name != 'node2':
            aggregator._output_queue.put(pattern)

    kwargs = {'aggregator': mocked_aggregated._aggregator}
    result = mocked_aggregated._aggregator._runner(task, 'pattern', **kwargs)
    assert result == ['pattern', 'pattern']


def test_aggregator_get_method(mocked_aggregated):
    """Test aggregator get method."""

    assert mocked_aggregated.get('pattern') == 'node2'


def test_aggregator_keys_method(mocked_aggregated):
    """Test aggregator keys method."""

    assert mocked_aggregated.keys('pattern') == ['node3', 'pattern']


def test_aggregator_set_method(mocked_aggregated):
    """Test aggregator set method."""

    mocked_aggregated.set('value', 'pattern')
    for node in mocked_aggregated._aggregator._redis_nodes:
        assert node.value == 'pattern'


def test_aggregator_delete_method(mocked_aggregated):
    """Test aggregator delete method."""

    mocked_aggregated.delete('pattern')
    for node in mocked_aggregated._aggregator._redis_nodes:
        assert not hasattr(node, 'name')


def test_loadbalanced_getitem_method(mocked_loadbalanced):
    """Test FlaskMultiRedis loadbalanced __getitem__ method."""

    assert mocked_loadbalanced['pattern'] in ['node1', 'node2', 'node3']
    mocked_loadbalanced._redis_nodes = []
    assert mocked_loadbalanced['pattern'] is None


def test_aggregated_getitem_method(mocked_aggregated):
    """Test FlaskMultiRedis aggregated __getitem__ method."""

    assert mocked_aggregated['pattern'] == 'node2'
    mocked_aggregated._aggregator._redis_nodes = []
    assert mocked_aggregated['pattern'] is None


def test_loadbalanced_setitem_method(mocked_loadbalanced):
    """Test FlaskMultiRedis loadbalanced __setitem__ method."""

    mocked_loadbalanced['name'] = 'node0'
    assert 'node0' in [x.name for x in mocked_loadbalanced._redis_nodes]
    mocked_loadbalanced._redis_nodes = []
    mocked_loadbalanced['name'] = 'node0'


def test_aggregated_setitem_method(mocked_aggregated):
    """Test FlaskMultiRedis aggregated __setitem__ method."""

    mocked_aggregated['name'] = 'node0'
    nodes = mocked_aggregated._aggregator._redis_nodes
    assert [x.name for x in nodes] == ['node0', 'node0', 'node0']
    mocked_aggregated._aggregator._redis_nodes = []
    mocked_aggregated['name'] = 'node0'


def test_loadbalanced_delitem_method(mocked_loadbalanced):
    """Test FlaskMultiRedis loadbalanced __delitem__ method."""

    del(mocked_loadbalanced['name'])
    for node in mocked_loadbalanced._redis_nodes:
        assert not hasattr(node, 'name')
    mocked_loadbalanced._redis_nodes = []
    del(mocked_loadbalanced['name'])


def test_aggregated_delitem_method(mocked_aggregated):
    """Test FlaskMultiRedis aggregated __delitem__ method."""

    del(mocked_aggregated['name'])
    for node in mocked_aggregated._aggregator._redis_nodes:
        assert not hasattr(node, 'name')
    mocked_aggregated._aggregator._redis_nodes = []
    del(mocked_aggregated['name'])
