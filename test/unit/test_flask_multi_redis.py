#! /usr/bin/env python
# -*- coding: utf-8 -*-

from sys import modules, version_info

if version_info >= (3,):
    from imp import reload


def test_redis_import_error():
    """Test that we can load FlaskMultiRedis even if redis module
    is not available."""

    import flask_multi_redis
    modules['redis'] = None
    flask_multi_redis = reload(flask_multi_redis)
    FlaskMultiRedis = flask_multi_redis.FlaskMultiRedis

    f = FlaskMultiRedis()
    assert f.provider_class is None


def test_constructor_app(mocker):
    """Test that the constructor passes the app to FlaskMultiRedis.init_app."""

    import flask_multi_redis
    del(modules['redis'])
    flask_multi_redis = reload(flask_multi_redis)
    FlaskMultiRedis = flask_multi_redis.FlaskMultiRedis

    mocker.patch.object(FlaskMultiRedis, 'init_app', autospec=True)
    app_stub = mocker.stub(name='app_stub')

    FlaskMultiRedis(app_stub)

    FlaskMultiRedis.init_app.assert_called_once_with(mocker.ANY, app_stub)
