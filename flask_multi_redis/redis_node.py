# -*- coding: utf-8 -*-

"""flask-multi-redis redis_node module."""


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
        for element in ['port', 'db', 'password', 'socket_timeout']:
            self.config[element] = config['default'][element]

            if element in config['node']:
                self.config[element] = config['node'][element]

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
