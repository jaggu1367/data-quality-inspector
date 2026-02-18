"""
Backwards-compatible re-export of HTML report functions.

Prefer: from dq_framework.reports import build_html_report, maybe_write_html_report, write_html_report
"""

from dq_framework.reports import (
    build_html_report,
    maybe_write_html_report,
    write_html_report,
)

__all__ = ["build_html_report", "maybe_write_html_report", "write_html_report"]
