"""Tests for schemadiff.notifier."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from schemadiff.notifier import NotifierConfig, NotifyError, notify
from schemadiff.summary import SchemaSummary


def _make_summary(total: int) -> SchemaSummary:
    return SchemaSummary(
        tables_added=total,
        tables_removed=0,
        columns_added=0,
        columns_removed=0,
        columns_modified=0,
    )


# ---------------------------------------------------------------------------
# notify() — callback path
# ---------------------------------------------------------------------------

def test_notify_calls_on_drift_callback():
    summary = _make_summary(2)
    cb = MagicMock()
    config = NotifierConfig(on_drift=cb)
    result = notify(summary, config)
    cb.assert_called_once_with(summary)
    assert result is True


def test_notify_skipped_below_min_severity():
    summary = _make_summary(0)
    cb = MagicMock()
    config = NotifierConfig(on_drift=cb, min_severity=1)
    result = notify(summary, config)
    cb.assert_not_called()
    assert result is False


def test_notify_respects_custom_min_severity():
    summary = _make_summary(3)
    cb = MagicMock()
    config = NotifierConfig(on_drift=cb, min_severity=5)
    result = notify(summary, config)
    cb.assert_not_called()
    assert result is False


def test_notify_returns_true_when_threshold_met():
    summary = _make_summary(5)
    cb = MagicMock()
    config = NotifierConfig(on_drift=cb, min_severity=5)
    result = notify(summary, config)
    cb.assert_called_once()
    assert result is True


# ---------------------------------------------------------------------------
# notify() — webhook path
# ---------------------------------------------------------------------------

def test_notify_posts_webhook(monkeypatch):
    summary = _make_summary(1)
    posted = {}

    def fake_post(url, payload):
        posted["url"] = url
        posted["payload"] = payload

    monkeypatch.setattr("schemadiff.notifier._post_webhook", fake_post)
    config = NotifierConfig(webhook_url="http://example.com/hook")
    result = notify(summary, config)
    assert result is True
    assert posted["url"] == "http://example.com/hook"
    assert posted["payload"]["total_changes"] == 1


def test_notify_webhook_raises_notify_error(monkeypatch):
    import urllib.error

    summary = _make_summary(1)

    def bad_post(url, payload):
        raise NotifyError("boom")

    monkeypatch.setattr("schemadiff.notifier._post_webhook", bad_post)
    config = NotifierConfig(webhook_url="http://bad.example.com/hook")
    with pytest.raises(NotifyError, match="boom"):
        notify(summary, config)


def test_notify_no_config_returns_false():
    summary = _make_summary(3)
    config = NotifierConfig()  # no webhook, no callback
    result = notify(summary, config)
    assert result is False
