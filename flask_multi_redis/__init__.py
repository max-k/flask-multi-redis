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
__version__ = '0.0.1'


class Aggregator(object):

    def __init__(self, redis_nodes):
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
                'timeout': node._config['socket_timeout']
            })
        for thread in threads:
            thread['worker'].join(thread['timeout'])
        while not self._output_queue.empty():
            item = self._output_queue.get()
            self._output_queue.task_done()
            results.append(item)
        if results != []:
            return results

    def get(self, pattern):
        def _get(node, pattern):
            result = node.get(pattern)
            if result:
                self._output_queue.put((node.ttl(pattern) or 1, result))
        results = self._runner(_get, pattern)
        if results:
            results.sort(key=lambda t: t[0])
            return results[-1][0]

    def keys(self, pattern):
        def _keys(node, pattern):
            results = node.keys(pattern)
            for result in results:
                self._output_queue.put(result)
        # return list(OrderedDict.fromkeys(self._runner(_keys, pattern)))
        return sorted(list(unique_everseen(self._runner(_keys, pattern))))

    def set(self, key, pattern, **kwargs):
        def _set(node, pattern, key=key, **kwargs):
            node.set(key, pattern, **kwargs)
        return self._runner(_set, pattern, **kwargs)

    def delete(self, pattern):
        def _delete(node, pattern):
            node.delete(pattern)
        return self._runner(_delete, pattern)

    def __getattr__(self, name):
        try:
            if name == '_redis_client':
                rnd = randint(0, len(self._redis_nodes) - 1)
                return getattr(self._redis_nodes[rnd], name)
            return getattr(self, name)
        except:
            message = '{} is not implemented yet.\n'.format(name)
            message += 'Feel free to contribute.'
            raise NotImplementedError(message)


class RedisNode(object):

    def __init__(self, provider_class, config, **kwargs):
        self._config = {}
        self._ssl = None
        self.provider_class = provider_class
        self._parse_conf(config)
        self._parse_ssl_conf(config)
        self._config.update(kwargs)
        self._redis_client = self.provider_class(**self._config)

    def _parse_conf(self, config):
        assert 'host' in config['node']

        self._config['host'] = config['node']['host']
        self._config['port'] = config['default']['port']
        self._config['db'] = config['default']['db']
        self._config['password'] = config['default']['password']
        self._config['socket_timeout'] = config['default']['socket_timeout']

        if 'port' in config['node']:
            self._config['port'] = config['node']['port']
        if 'db' in config['node']:
            self._config['db'] = config['node']['db']
        if 'password' in config['node']:
            self._config['password'] = config['node']['password']
        if 'timeout' in config['node']:
            self._config['socket_timeout'] = config['node']['timeout']

    def _parse_ssl_conf(self, config):
        self._config['ssl'] = False

        if 'ssl' in config['default']:
            self._config['ssl'] = True
            self._ssl = config['default']['ssl']
        if 'ssl' in config['node']:
            if not self._ssl:
                self._ssl = {}
            for key in config['node']['ssl']:
                self._ssl[key] = config['node']['ssl'][key]
        if self._ssl:
            self._config.update(self._ssl)

    def __getattr__(self, name):
        return getattr(self._redis_client, name)


class FlaskMultiRedis(object):

    def __init__(self, app=None, strict=True,
                 config_prefix='REDIS', strategy='loadbalancing', **kwargs):
        assert strategy in ['loadbalancing', 'aggregate']
        self._redis_nodes = []
        self._strategy = strategy
        self._aggregator = None
        self.provider_class = redis.StrictRedis if strict else redis.Redis
        self.provider_kwargs = kwargs
        self.config_prefix = config_prefix

        if app is not None:
            self.init_app(app)

    @classmethod
    def from_custom_provider(cls, provider, app=None, **kwargs):
        assert provider is not None, 'your custom provider is None, come on'

        # We never pass the app parameter here, so we can call init_app
        # ourselves later, after the provider class has been set
        instance = cls(**kwargs)

        instance.provider_class = provider
        if app is not None:
            instance.init_app(app)
        return instance

    def init_app(self, app, **kwargs):

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
        if name == '_redis_client' and len(self._redis_nodes) == 0:
            return None
        if self._strategy == 'aggregate':
            return getattr(self._aggregator, name)
        else:
            rnd = randint(0, len(self._redis_nodes) - 1)
            return getattr(self._redis_nodes[rnd], name)

    def __getitem__(self, name):
        if len(self._redis_nodes) == 0:
            return None
        return self.get(name)

    def __setitem__(self, name, value):
        if len(self._redis_nodes) == 0:
            return
        return self.set(name, value)

    def __delitem__(self, name):
        if len(self._redis_nodes) == 0:
            return
        return self.delete(name)
