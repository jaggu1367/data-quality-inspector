"""
Backwards-compatible re-export of email report functions.

Prefer: from dq_framework.reports import load_reports_config, send_email_report
"""

from dq_framework.reports import load_reports_config, send_email_report

__all__ = ["load_reports_config", "send_email_report"]
