"""Notification hooks for schema drift events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Callable, Optional

from schemadiff.summary import SchemaSummary


@dataclass
class NotifierConfig:
    """Configuration for a drift notifier."""
    webhook_url: Optional[str] = None
    on_drift: Optional[Callable[[SchemaSummary], None]] = None
    min_severity: int = 1  # minimum total_changes to trigger notification


class NotifyError(Exception):
    """Raised when a notification attempt fails."""


def _post_webhook(url: str, payload: dict) -> None:
    """Send a JSON POST request to *url* with *payload*."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.URLError as exc:
        raise NotifyError(f"Webhook POST failed: {exc}") from exc


def notify(summary: SchemaSummary, config: NotifierConfig) -> bool:
    """Dispatch drift notifications according to *config*.

    Returns True if at least one notification was sent, False otherwise.
    """
    if summary.total_changes < config.min_severity:
        return False

    sent = False

    if config.webhook_url:
        payload = summary.to_dict()
        _post_webhook(config.webhook_url, payload)
        sent = True

    if config.on_drift is not None:
        config.on_drift(summary)
        sent = True

    return sent
