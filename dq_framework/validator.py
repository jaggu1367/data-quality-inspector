"""
Backwards-compatible re-export of DataQualityValidator.

Prefer: from dq_framework.services import DataQualityValidator
"""

from dq_framework.services import DataQualityValidator

__all__ = ["DataQualityValidator"]
