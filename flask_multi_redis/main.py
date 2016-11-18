# -*- coding: utf-8 -*-

"""flask-multi-redis main module."""

from random import randint

try:
    import redis
except ImportError:
    # We can allow custom provider only usage without redis-py being installed
    redis = None

from flask_multi_redis.aggregator import Aggregator
from flask_multi_redis.redis_node import RedisNode


class FlaskMultiRedis(object):

    """Main Class for FlaskMultiRedis."""

    def __init__(self, app=None, strict=True,
                 config_prefix='REDIS', strategy='loadbalancing', **kwargs):
        """Initialize FlaskMultiRedis."""
        assert strategy in ['loadbalancing', 'aggregate']
        self._app = None
        self._redis_nodes = []
        self._strategy = strategy
        self._aggregator = None
        self.provider_class = None
        if redis:
            self.provider_class = redis.StrictRedis if strict else redis.Redis
        self.provider_kwargs = kwargs
        self.config_prefix = config_prefix

        if app is not None:
            self.init_app(app)

    @classmethod
    def from_custom_provider(cls, provider, app=None, **kwargs):
        """Create a FlaskMultiRedis instance using a custom Redis provider."""
        assert provider is not None, 'your custom provider is None, come on'

        # We never pass the app parameter here, so we can call init_app
        # ourselves later, after the provider class has been set
        instance = cls(**kwargs)

        instance.provider_class = provider
        if app is not None:
            instance.init_app(app)
        return instance

    def init_app(self, app, **kwargs):
        """Initialize Flask app and parse configuration."""
        self._app = app
        self.provider_kwargs.update(kwargs)

        redis_default_port = app.config.get(
            '{0}_DEFAULT_PORT'.format(self.config_prefix), 6379
        )
        redis_default_db = app.config.get(
            '{0}_DEFAULT_DB'.format(self.config_prefix), 0
        )
        redis_default_password = app.config.get(
            '{0}_DEFAULT_PASSWORD'.format(self.config_prefix), None
        )
        redis_default_socket_timeout = app.config.get(
            '{0}_DEFAULT_SOCKET_TIMEOUT'.format(self.config_prefix), 5
        )
        redis_default_ssl = app.config.get(
            '{0}_DEFAULT_SSL'.format(self.config_prefix), None
        )

        redis_nodes = app.config.get(
            '{0}_NODES'.format(self.config_prefix), [
                {
                    'host': 'localhost',
                }
            ]
        )

        default_conf = {
            'port': redis_default_port,
            'db': redis_default_db,
            'password': redis_default_password,
            'socket_timeout': redis_default_socket_timeout,
            'ssl': redis_default_ssl
        }

        for redis_node in redis_nodes:
            conf = {
                'node': redis_node,
                'default': default_conf
            }
            nod = RedisNode(self.provider_class, conf, **self.provider_kwargs)
            self._redis_nodes.append(nod)

        if self._strategy == 'aggregate':
            self._aggregator = Aggregator(self._redis_nodes)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['redis'] = self

    def __getattr__(self, name):
        if len(self._redis_nodes) == 0:
            return None
        if self._strategy == 'aggregate':
            return getattr(self._aggregator, name)
        else:
            rnd = randint(0, len(self._redis_nodes) - 1)
            return getattr(self._redis_nodes[rnd], name)

    def __getitem__(self, name):
        if len(self._redis_nodes) == 0:
            return None
        if self._strategy == 'aggregate':
            return self._aggregator.get(name)
        else:
            rnd = randint(0, len(self._redis_nodes) - 1)
            return self._redis_nodes[rnd].get(name)

    def __setitem__(self, name, value):
        if len(self._redis_nodes) == 0:
            return
        if self._strategy == 'aggregate':
            return self._aggregator.set(name, value)
        else:
            rnd = randint(0, len(self._redis_nodes) - 1)
            return self._redis_nodes[rnd].set(name, value)

    def __delitem__(self, name):
        if len(self._redis_nodes) == 0:
            return
        if self._strategy == 'aggregate':
            return self._aggregator.delete(name)
        else:
            for node in self._redis_nodes:
                node.delete(name)
