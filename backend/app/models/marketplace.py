"""
Compatibility module.

Before, this repo defined `Vendor`, `Customer`, and `Package` in this file.
The models are now split across individual modules (Java-style, one entity per file),
but many services still import from `app.models.marketplace`.
"""

from app.models.customer import Customer
from app.models.package import Package
from app.models.vendor import Vendor

__all__ = ["Customer", "Package", "Vendor"]

