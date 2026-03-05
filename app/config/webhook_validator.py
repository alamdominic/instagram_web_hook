"""Pydantic models for the Instagram webhook payload."""

from typing import Any
from pydantic import BaseModel


class Change(BaseModel):
    """Represent a single changed field in a webhook event.

    Attributes:
        field (str): Field name (for example, comments or mentions).
        value (Any): Field payload.
    """

    field: str
    value: Any


class Entry(BaseModel):
    """Represent a top-level entry in the webhook payload.

    Attributes:
        id (str): Entry id.
        time (int): Unix timestamp in seconds.
        changes (list[Change]): List of changes within the entry.
    """

    id: str
    time: int
    changes: list[Change]


class WebhookPayload(BaseModel):
    """Root payload model for Instagram/Meta webhooks.

    Attributes:
        object (str): Object type, expected to be "instagram".
        entry (list[Entry]): Entries included in the webhook.
    """

    object: str
    entry: list[Entry]
