"""
Unit tests for BaseAdapter, StaticAdapter, and AdapterFactory (Task 3.1)
Validates: Requirements 2.6, 2.7, 6.3
"""
import os
import pytest
import sys
from unittest.mock import patch, MagicMock
import requests as req

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from VG_Extractor import BaseAdapter, StaticAdapter, AdapterFactory, AdapterError, JS_DOMAINS


# ── BaseAdapter ───────────────────────────────────────────────────────────────

def test_base_adapter_is_abstract():
    """BaseAdapter cannot be instantiated directly (it's abstract)."""
    with pytest.raises(TypeError):
        BaseAdapter()


def test_base_adapter_subclass_must_implement_fetch_page():
    """A subclass that doesn't implement fetch_page cannot be instantiated."""
    class IncompleteAdapter(BaseAdapter):
        pass

    with pytest.raises(TypeError):
        IncompleteAdapter()


# ── StaticAdapter ─────────────────────────────────────────────────────────────

def test_static_adapter_is_subclass_of_base():
    """StaticAdapter is a subclass of BaseAdapter."""
    assert issubclass(StaticAdapter, BaseAdapter)


def test_static_adapter_timeout_value():
    """StaticAdapter.TIMEOUT is 10 seconds (Requirement 2.6)."""
    assert StaticAdapter.TIMEOUT == 10


def test_static_adapter_has_user_agent():
    """StaticAdapter.HEADERS contains a User-Agent string."""
    assert 'User-Agent' in StaticAdapter.HEADERS
    assert StaticAdapter.HEADERS['User-Agent']


def test_static_adapter_timeout_raises_adapter_error():
    """A timeout raises AdapterError (Requirement 2.7)."""
    with patch("requests.get", side_effect=req.exceptions.Timeout):
        adapter = StaticAdapter()
        with pytest.raises(AdapterError) as exc_info:
            adapter.fetch_page("https://example.com/")
        assert "Timeout" in str(exc_info.value)


def test_static_adapter_http_error_raises_adapter_error():
    """An HTTP error (4xx/5xx) raises AdapterError (Requirement 2.7)."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = req.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error

    with patch("requests.get", return_value=mock_response):
        adapter = StaticAdapter()
        with pytest.raises(AdapterError) as exc_info:
            adapter.fetch_page("https://example.com/")
        assert "404" in str(exc_info.value)


def test_static_adapter_network_error_raises_adapter_error():
    """A generic network error raises AdapterError (Requirement 6.3)."""
    with patch("requests.get", side_effect=req.exceptions.ConnectionError("refused")):
        adapter = StaticAdapter()
        with pytest.raises(AdapterError):
            adapter.fetch_page("https://example.com/")


def test_static_adapter_returns_html_on_success():
    """StaticAdapter returns the response text on a successful request."""
    mock_response = MagicMock()
    mock_response.text = "<html><body>Hello</body></html>"
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response):
        adapter = StaticAdapter()
        result = adapter.fetch_page("https://example.com/")
    assert result == "<html><body>Hello</body></html>"


# ── AdapterFactory ────────────────────────────────────────────────────────────

def test_adapter_factory_returns_static_adapter_by_default():
    """AdapterFactory returns StaticAdapter for a regular domain."""
    factory = AdapterFactory()
    adapter = factory.get_adapter("https://www.as.com/real_madrid/")
    assert isinstance(adapter, StaticAdapter)


def test_adapter_factory_returns_static_for_unknown_domain():
    """AdapterFactory returns StaticAdapter for any domain not in JS_DOMAINS."""
    factory = AdapterFactory()
    adapter = factory.get_adapter("https://www.marca.com/futbol/")
    assert isinstance(adapter, StaticAdapter)


def test_adapter_factory_strips_www_prefix():
    """AdapterFactory correctly strips 'www.' when matching domains."""
    factory = AdapterFactory()
    # marca.com is not a JS domain, so should return StaticAdapter
    adapter = factory.get_adapter("https://www.marca.com/")
    assert isinstance(adapter, StaticAdapter)


def test_js_domains_set_contains_expected_domains():
    """JS_DOMAINS contains the expected JavaScript-rendered sites."""
    assert "realmadrid.com" in JS_DOMAINS
    assert "laliga.com" in JS_DOMAINS


# ── PlaywrightAdapter ─────────────────────────────────────────────────────────

def test_playwright_adapter_not_installed():
    """PlaywrightAdapter raises AdapterError with install instructions when Playwright is missing (Requirement 2.7)."""
    from VG_Extractor import PlaywrightAdapter

    original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

    def mock_import(name, *args, **kwargs):
        if name == "playwright.sync_api":
            raise ImportError("No module named 'playwright'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        adapter = PlaywrightAdapter()
        with pytest.raises(AdapterError) as exc_info:
            adapter.fetch_page("https://realmadrid.com/")

    error_msg = str(exc_info.value)
    assert "Playwright" in error_msg
    assert "pip install playwright" in error_msg or "install" in error_msg.lower()
