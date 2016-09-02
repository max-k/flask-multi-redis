# -*- coding: utf-8 -*-

"""Main flask-multi-redis module."""

from itertools import chain
from random import randint
from sys import version_info
from threading import Thread

from more_itertools import unique_everseen

# from collections import OrderedDict

try:
    import redis
except ImportError:
    # We can allow custom provider only usage without redis-py being installed
    redis = None

if version_info < (3,):
    import Queue as queue
else:
    import queue


__all__ = ('Aggregator', 'RedisNode', 'FlaskMultiRedis')
__version__ = '0.1.4'


class Aggregator(object):

    """Reimplement Redis commands with aggregation from multiple servers."""

    def __init__(self, redis_nodes):
        """Initialize Aggregator."""
        self._output_queue = queue.Queue()
        self._redis_nodes = redis_nodes

    def _runner(self, target, pattern, **kwargs):
        threads = []
        results = []
        for node in self._redis_nodes:
            worker = Thread(target=target, args=(node, pattern), kwargs=kwargs)
            worker.start()
            threads.append({
                'worker': worker,
                'timeout': node.config['socket_timeout']
            })
        for thread in threads:
            thread['worker'].join(thread['timeout'])
        while not self._output_queue.empty():
            item = self._output_queue.get()
            self._output_queue.task_done()
            results.append(item)
        if results != [] or target.__name__ == '_keys':
            if target.__name__ == '_scan_iter':
                return chain(*results)
            if target.__name__ == '_delete':
                return sum([x for x in results if isinstance(x, int)])
            if target.__name__ == '_set':
                return len(set(results)) <= 1
            return results

    def get(self, pattern):
        """Aggregated get method."""
        def _get(node, pattern):
            result = node.get(pattern)
            if result:
                self._output_queue.put((node.ttl(pattern) or 1, result))
        results = self._runner(_get, pattern)
        if results:
            results.sort(key=lambda t: t[0])
            return results[-1][1]

    def keys(self, pattern):
        """Aggregated keys method."""
        def _keys(node, pattern):
            for result in node.keys(pattern):
                self._output_queue.put(result)
        # return list(OrderedDict.fromkeys(self._runner(_keys, pattern)))
        return sorted(list(unique_everseen(self._runner(_keys, pattern))))

    def set(self, key, pattern, **kwargs):
        """Aggregated set method."""
        def _set(node, pattern, key=key, **kwargs):
            self._output_queue.put(node.set(key, pattern, **kwargs))
        return self._runner(_set, pattern, **kwargs)

    def delete(self, pattern):
        """Aggregated delete method."""
        def _delete(node, pattern):
            self._output_queue.put(node.delete(pattern))
        return self._runner(_delete, pattern)

    def scan_iter(self, pattern):
        """Aggregated scan_iter method."""
        def _scan_iter(node, pattern):
            self._output_queue.put(node.scan_iter(pattern))
        return self._runner(_scan_iter, pattern)

    def __getattr__(self, name):
        if name in ['_redis_client', 'connection_pool']:
            if len(self._redis_nodes) == 0:
                return None
            rnd = randint(0, len(self._redis_nodes) - 1)
            return getattr(self._redis_nodes[rnd], name)
        else:
            message = '{0} is not implemented yet.'.format(name)
            message += ' Feel free to contribute.'
            raise NotImplementedError(message)


class RedisNode(object):

    """Define a Redis node and its configuration."""

    def __init__(self, provider_class, config, **kwargs):
        """Initialize RedisNode."""
        self.config = {}
        self._ssl = None
        self.provider_class = provider_class
        self._parse_conf(config)
        self._parse_ssl_conf(config)
        self.config.update(kwargs)
        self._redis_client = self.provider_class(**self.config)

    def _parse_conf(self, config):
        assert 'host' in config['node']

        self.config['host'] = config['node']['host']
        self.config['port'] = config['default']['port']
        self.config['db'] = config['default']['db']
        self.config['password'] = config['default']['password']
        self.config['socket_timeout'] = config['default']['socket_timeout']

        if 'port' in config['node']:
            self.config['port'] = config['node']['port']
        if 'db' in config['node']:
            self.config['db'] = config['node']['db']
        if 'password' in config['node']:
            self.config['password'] = config['node']['password']
        if 'timeout' in config['node']:
            self.config['socket_timeout'] = config['node']['timeout']

    def _parse_ssl_conf(self, config):
        self.config['ssl'] = False

        if 'ssl' in config['default']:
            self.config['ssl'] = True
            self._ssl = config['default']['ssl']
        if 'ssl' in config['node']:
            if not self._ssl:
                self._ssl = {}
            for key in config['node']['ssl']:
                self._ssl[key] = config['node']['ssl'][key]
        if self._ssl:
            self.config.update(self._ssl)

    def __getattr__(self, name):
        return getattr(self._redis_client, name)


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
