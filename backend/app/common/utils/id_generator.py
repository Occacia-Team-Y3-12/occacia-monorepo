from __future__ import annotations

from uuid import uuid4


def generate_prefixed_id(prefix: str) -> str:
    """
    Generate an application-level string ID in the format: "{prefix}-{UniqueID}".
    Example: "CUS-9f2c1b3a4d5e6f7a8b9c0d1e2f3a4b5c".
    """
    cleaned_prefix = prefix.strip().upper()
    if not cleaned_prefix:
        raise ValueError("prefix must be a non-empty string")
    return f"{cleaned_prefix}-{uuid4().hex}"

