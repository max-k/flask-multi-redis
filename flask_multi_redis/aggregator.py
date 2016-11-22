# -*- coding: utf-8 -*-

"""flask-multi-redis aggregator module."""

from itertools import chain
from random import randint
from sys import version_info
from threading import Thread

from more_itertools import unique_everseen

# from collections import OrderedDict

if version_info < (3,):
    import Queue as queue
else:
    import queue


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
        results = self._runner(_keys, pattern)
        # return list(OrderedDict.fromkeys(results))
        return sorted(list(unique_everseen(results)))

    def set(self, key, pattern, **kwargs):
        """Aggregated set method."""
        def _set(node, pattern, key=key, **kwargs):
            self._output_queue.put(node.set(key, pattern, **kwargs))
        results = self._runner(_set, pattern, **kwargs)
        return len(set(results)) <= 1

    def _aggregated_put(self, pattern, method):
        """Default aggregated put method."""
        def _aggregated_method(node, pattern):
            _method = getattr(node, method)
            self._output_queue.put(_method(pattern))
        return self._runner(_aggregated_method, pattern)

    def delete(self, pattern):
        """Aggregated delete method."""
        results = self._aggregated_put(pattern, 'delete')
        return sum([x for x in results if isinstance(x, int)])

    def scan_iter(self, pattern):
        """Aggregated scan_iter method."""
        results = self._aggregated_put(pattern, 'scan_iter')
        print(results)
        return chain(*results)

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
