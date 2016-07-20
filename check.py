#! //usr/bin/env python
import flask
from flask_multi_redis import FlaskMultiRedis
from mockredis import MockRedis

app = flask.Flask(__name__)

app.config['REDIS_NODES'] = [
    {
        'host': 'ref02-bis.prod.cfengine.s1.p.fti.net'
    },
    {
        'host': 'ref02-bis.prod.cfengine.b2.p.fti.net'
    },
    {
        'host': 'ref02-bis.prod.cfengine.m1.p.fti.net'
    }
]

redis_store = FlaskMultiRedis.from_custom_provider(MockRedis, app, strategy='aggregate')
redis_store.set('clee', 'valeure')
redis_store.set('cle', 'valeur')
redis_store.set('cle2', 'valeur2')
redis_store.delete('clee')
print(redis_store.get('cle'))
print(redis_store.get('clee'))
print(redis_store.keys('*'))
