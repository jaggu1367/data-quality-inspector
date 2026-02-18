"""
Reports module: HTML and email report generation.
"""

from dq_framework.reports.config import load_reports_config
from dq_framework.reports.email_report import send_email_report
from dq_framework.reports.html_report import (
    build_html_report,
    maybe_write_html_report,
    write_html_report,
)

__all__ = [
    "load_reports_config",
    "send_email_report",
    "build_html_report",
    "maybe_write_html_report",
    "write_html_report",
]
