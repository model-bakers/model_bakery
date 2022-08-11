"""Utility functions to manage timezone code."""

from datetime import datetime, timezone

from django.conf import settings


def tz_aware(value: datetime) -> datetime:
    """Return an UTC-aware datetime in case of USE_TZ=True."""
    if settings.USE_TZ:
        value = value.replace(tzinfo=timezone.utc)

    return value
