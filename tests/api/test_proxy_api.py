# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testProxyApi.py
   Description :   Flask API全路由测试
   Author :        JHao
   date：          2026/5/28
-------------------------------------------------
   Change Activity:
                   2026/05/28:
-------------------------------------------------
"""
__author__ = 'JHao'

import pytest
from unittest.mock import patch, MagicMock
from helper.proxy import Proxy
from api.proxyApi import JsonResponse


@pytest.fixture
def mocks(app):
    """快捷访问 app._test_mocks"""
    return app._test_mocks


class TestIndex:

    def test_index_returns_api_list(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "url" in data
        assert len(data["url"]) > 0


class TestGet:

    def test_get_returns_proxy(self, client, mocks):
        proxy = Proxy("1.2.3.4:8080", source="test", https=False)
        mocks["get"].return_value = proxy

        resp = client.get("/get/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["proxy"] == "1.2.3.4:8080"
        assert data["https"] is False

    def test_get_no_proxy(self, client, mocks):
        mocks["get"].return_value = None

        resp = client.get("/get/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 0
        assert data["src"] == "no proxy"

    def test_get_https_filter(self, client, mocks):
        proxy = Proxy("5.6.7.8:443", source="test", https=True)
        mocks["get"].return_value = proxy

        resp = client.get("/get/?type=https")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["https"] is True
        mocks["get"].assert_called_with(https=True, residential=None)

    def test_get_http_filter(self, client, mocks):
        mocks["get"].return_value = None

        client.get("/get/")
        mocks["get"].assert_called_with(https=False, residential=None)

    def test_get_residential_filter(self, client, mocks):
        proxy = Proxy("1.1.1.1:8080", source="test", is_residential=True)
        mocks["get"].return_value = proxy

        resp = client.get("/get/?residential=true")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_residential"] is True
        mocks["get"].assert_called_with(https=False, residential=True)

    def test_get_residential_false_filter(self, client, mocks):
        proxy = Proxy("1.1.1.1:8080", source="test", is_residential=False)
        mocks["get"].return_value = proxy

        resp = client.get("/get/?residential=false")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_residential"] is False
        mocks["get"].assert_called_with(https=False, residential=False)

    def test_get_type_residential(self, client, mocks):
        proxy = Proxy("1.1.1.1:8080", source="test", is_residential=True)
        mocks["get"].return_value = proxy

        resp = client.get("/get/?type=residential")
        assert resp.status_code == 200
        mocks["get"].assert_called_with(https=False, residential=True)


class TestPop:

    def test_pop_returns_proxy(self, client, mocks):
        proxy = Proxy("1.2.3.4:8080", source="test")
        mocks["pop"].return_value = proxy

        resp = client.get("/pop/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["proxy"] == "1.2.3.4:8080"
        mocks["pop"].assert_called_with(https=False, residential=None)

    def test_pop_residential_filter(self, client, mocks):
        proxy = Proxy("1.2.3.4:8080", source="test", is_residential=True)
        mocks["pop"].return_value = proxy

        resp = client.get("/pop/?residential=1")
        assert resp.status_code == 200
        mocks["pop"].assert_called_with(https=False, residential=True)

    def test_pop_residential_false_filter(self, client, mocks):
        proxy = Proxy("1.2.3.4:8080", source="test", is_residential=False)
        mocks["pop"].return_value = proxy

        resp = client.get("/pop/?residential=false")
        assert resp.status_code == 200
        mocks["pop"].assert_called_with(https=False, residential=False)

    def test_pop_no_proxy(self, client, mocks):
        mocks["pop"].return_value = None

        resp = client.get("/pop/")
        data = resp.get_json()
        assert data["code"] == 0


class TestAll:

    def test_all_returns_list(self, client, mocks):
        proxies = [
            Proxy("1.2.3.4:8080", source="test"),
            Proxy("5.6.7.8:443", source="test", https=True),
        ]
        mocks["getAll"].return_value = proxies

        resp = client.get("/all/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["proxy"] == "1.2.3.4:8080"
        assert data[1]["proxy"] == "5.6.7.8:443"

    def test_all_residential_filter(self, client, mocks):
        proxies = [Proxy("1.1.1.1:8080", source="test", is_residential=True)]
        mocks["getAll"].return_value = proxies

        resp = client.get("/all/?residential=true")
        assert resp.status_code == 200
        mocks["getAll"].assert_called_with(https=False, residential=True, num=None)

    def test_all_residential_false_filter(self, client, mocks):
        proxies = [Proxy("1.1.1.1:8080", source="test", is_residential=False)]
        mocks["getAll"].return_value = proxies

        resp = client.get("/all/?residential=false")
        assert resp.status_code == 200
        mocks["getAll"].assert_called_with(https=False, residential=False, num=None)

    def test_all_num_filter(self, client, mocks):
        proxies = [Proxy("1.1.1.1:8080", source="test")]
        mocks["getAll"].return_value = proxies

        resp = client.get("/all/?num=1")
        assert resp.status_code == 200
        mocks["getAll"].assert_called_with(https=False, residential=None, num=1)

    def test_all_residential_false_and_num_filter(self, client, mocks):
        proxies = [Proxy("1.1.1.1:8080", source="test", is_residential=False)]
        mocks["getAll"].return_value = proxies

        resp = client.get("/all/?residential=false&num=1")
        assert resp.status_code == 200
        mocks["getAll"].assert_called_with(https=False, residential=False, num=1)

    def test_all_empty(self, client, mocks):
        mocks["getAll"].return_value = []

        resp = client.get("/all/")
        data = resp.get_json()
        assert data == []


class TestDelete:

    def test_delete_calls_handler(self, client, mocks):
        mocks["delete"].return_value = True

        resp = client.get("/delete/?proxy=1.2.3.4:8080")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 0
        assert data["src"] is True
        mocks["delete"].assert_called_once()


class TestCount:

    def test_count_returns_stats(self, client, mocks):
        proxies = [
            Proxy("1.2.3.4:8080", source="freeProxy01", https=False, is_residential=False),
            Proxy("5.6.7.8:443", source="freeProxy02", https=True, is_residential=True),
        ]
        mocks["getAll"].return_value = proxies

        resp = client.get("/count/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 2
        assert data["residential"] == 1
        assert data["http_type"]["http"] == 1
        assert data["http_type"]["https"] == 1
        assert data["source"]["freeProxy01"] == 1
        assert data["source"]["freeProxy02"] == 1

    def test_count_empty(self, client, mocks):
        mocks["getAll"].return_value = []

        resp = client.get("/count/")
        data = resp.get_json()
        assert data["count"] == 0
        assert data["residential"] == 0
        assert data["http_type"] == {}
        assert data["source"] == {}


class TestTokenAuth:

    def test_token_auth_missing(self, client):
        with patch("api.proxyApi.conf.authToken", "secret-token"):
            resp = client.get("/get/")
            assert resp.status_code == 401
            data = resp.get_json()
            assert data["code"] == 401

    def test_token_auth_invalid(self, client):
        with patch("api.proxyApi.conf.authToken", "secret-token"):
            resp = client.get("/get/", headers={"Authorization": "Bearer wrong-token"})
            assert resp.status_code == 401

    def test_token_auth_valid_bearer_header(self, client, mocks):
        mocks["get"].return_value = Proxy("1.2.3.4:8080")
        with patch("api.proxyApi.conf.authToken", "secret-token"):
            resp = client.get("/get/", headers={"Authorization": "Bearer secret-token"})
            assert resp.status_code == 200

    def test_token_auth_valid_x_api_token(self, client, mocks):
        mocks["get"].return_value = Proxy("1.2.3.4:8080")
        with patch("api.proxyApi.conf.authToken", "secret-token"):
            resp = client.get("/get/", headers={"X-API-Token": "secret-token"})
            assert resp.status_code == 200

    def test_token_auth_query_param_rejected(self, client, mocks):
        # Query-string tokens are no longer accepted (leak into URLs/logs).
        mocks["get"].return_value = Proxy("1.2.3.4:8080")
        with patch("api.proxyApi.conf.authToken", "secret-token"):
            resp = client.get("/get/?token=secret-token")
            assert resp.status_code == 401

    def test_token_auth_valid_x_auth_token(self, client, mocks):
        mocks["get"].return_value = Proxy("1.2.3.4:8080")
        with patch("api.proxyApi.conf.authToken", "secret-token"):
            resp = client.get("/get/", headers={"X-Auth-Token": "secret-token"})
            assert resp.status_code == 200


class TestRefresh:

    def test_refresh_returns_success(self, client):
        resp = client.get("/refresh/")
        assert resp.status_code == 200
        assert b"success" in resp.data


class TestJsonResponse:

    def test_force_type_with_dict(self, app):
        """dict -> JSON Response"""
        with app.app_context():
            resp = JsonResponse.force_type({"key": "val"})
            assert resp.content_type == "application/json"

    def test_force_type_with_list(self, app):
        """list -> JSON Response"""
        with app.app_context():
            resp = JsonResponse.force_type([1, 2, 3])
            assert resp.content_type == "application/json"


class TestRunFlask:

    @patch("api.proxyApi.platform")
    @patch("api.proxyApi.app")
    def test_runflask_windows_path(self, mock_app, mock_platform):
        """Windows 下调用 app.run()，TLS 关闭时 ssl_context=None"""
        mock_platform.system.return_value = "Windows"
        with patch("api.proxyApi.conf.sslEnabled", False):
            from api.proxyApi import runFlask
            runFlask()
        mock_app.run.assert_called_once()
        assert mock_app.run.call_args.kwargs.get("ssl_context") is None

    @patch("api.proxyApi.platform")
    @patch("api.proxyApi.app")
    def test_runflask_exits_when_tls_enabled_without_cert(self, mock_app, mock_platform):
        """SSL_ENABLED 但证书缺失时应退出"""
        mock_platform.system.return_value = "Windows"
        with patch("api.proxyApi.conf.sslEnabled", True), \
             patch("api.proxyApi.conf.sslCertFile", "/nope/tls.crt"), \
             patch("api.proxyApi.conf.sslKeyFile", "/nope/tls.key"):
            from api.proxyApi import runFlask
            with pytest.raises(SystemExit):
                runFlask()