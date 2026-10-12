"""Utility functions to manage timezone code."""

from datetime import UTC, datetime

from django.conf import settings


def tz_aware(value: datetime) -> datetime:
    """Return an UTC-aware datetime in case of USE_TZ=True."""
    if settings.USE_TZ:
        return value.replace(tzinfo=UTC)

    return value.replace(tzinfo=None)
