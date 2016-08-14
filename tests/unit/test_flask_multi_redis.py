#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask_multi_redis import FlaskMultiRedis


def test_constructor_app(mocker):
    """Test that the constructor passes the app to FlaskMultiRedis.init_app."""
    mocker.patch.object(FlaskMultiRedis, 'init_app', autospec=True)
    app_stub = mocker.stub(name='app_stub')

    FlaskMultiRedis(app_stub)

    FlaskMultiRedis.init_app.assert_called_once_with(mocker.ANY, app_stub)
