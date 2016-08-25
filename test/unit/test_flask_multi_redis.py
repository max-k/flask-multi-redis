#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.modules['redis'] = None


def test_redis_import_error():
    """Test that we can load FlaskMultiRedis even if redis module
    is not available."""

    from flask_multi_redis import FlaskMultiRedis
    f = FlaskMultiRedis()
    assert f.provider_class is None


def test_constructor_app(mocker):
    """Test that the constructor passes the app to FlaskMultiRedis.init_app."""

    from flask_multi_redis import FlaskMultiRedis
    mocker.patch.object(FlaskMultiRedis, 'init_app', autospec=True)
    app_stub = mocker.stub(name='app_stub')

    FlaskMultiRedis(app_stub)

    FlaskMultiRedis.init_app.assert_called_once_with(mocker.ANY, app_stub)
