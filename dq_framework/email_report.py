"""
Email report for data quality validations.
Two layers: (1) Input data source details, (2) Data quality report.
Configuration in config/dq_report_config.json.
"""
import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional


def load_reports_config(config_path: str, root_dir: str) -> dict:
    """Load reports config from JSON file."""
    path = config_path if os.path.isabs(config_path) else os.path.join(root_dir, config_path)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_source_details_layer(source_info: Dict[str, Any]) -> str:
    """Layer 1: Input data source details."""
    lines = [
        "=" * 50,
        "LAYER 1: INPUT DATA SOURCE",
        "=" * 50,
        "",
        f"Data Source Name:  {source_info.get('data_source_name', 'N/A')}",
        f"Source Type:       {source_info.get('source_type', 'N/A')}",
        f"Path/Table:        {source_info.get('path_or_table', 'N/A')}",
        f"Row Count:         {source_info.get('row_count', 0)}",
        f"Columns:           {source_info.get('columns', [])}",
        f"Validation Time:   {source_info.get('timestamp', 'N/A')}",
        "",
    ]
    return "\n".join(lines)


def build_dq_report_layer(dq_report: Dict[str, Any]) -> str:
    """Layer 2: Data quality report."""
    summary = dq_report.get("summary", {})
    total = summary.get("total_rules", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    overall = "PASSED" if dq_report.get("success", False) else "FAILED"

    lines = [
        "=" * 50,
        "LAYER 2: DATA QUALITY REPORT",
        "=" * 50,
        "",
        f"Overall Status:    {overall}",
        f"Total Rules:       {total}",
        f"Passed:            {passed}",
        f"Failed:            {failed}",
        "",
        "Per-rule results:",
        "-" * 40,
    ]

    for rule_name, rule_result in dq_report.get("results", {}).items():
        ok = rule_result.get("success", False)
        status = "PASS" if ok else "FAIL"
        lines.append(f"  [{status}] {rule_name}")
        if not ok:
            exc = rule_result.get("exception_info")
            if exc:
                lines.append(f"       Error: {(exc or '')[:150]}")
            else:
                res = rule_result.get("result") or {}
                inner = res.get("result") if isinstance(res, dict) else res
                if isinstance(inner, dict) and "unexpected_count" in inner:
                    lines.append(f"       Unexpected count: {inner['unexpected_count']}")

    lines.append("")
    return "\n".join(lines)


def build_email_body(source_info: Dict[str, Any], dq_report: Dict[str, Any]) -> str:
    """Build full email body with both layers."""
    layer1 = build_source_details_layer(source_info)
    layer2 = build_dq_report_layer(dq_report)
    return layer1 + "\n" + layer2


def send_email_report(
    source_info: Dict[str, Any],
    dq_report: Dict[str, Any],
    config_path: str = "config/dq_report_config.json",
    root_dir: Optional[str] = None,
) -> bool:
    """
    Send data quality report email. Returns True if sent, False if skipped or failed.
    """
    root = root_dir or os.getcwd()
    config = load_reports_config(config_path, root)
    email_cfg = config.get("email", {})
    if not email_cfg.get("enabled", False):
        return False

    to_addresses = email_cfg.get("to_addresses") or []
    if not to_addresses:
        return False

    subject_template = email_cfg.get("subject", "Data Quality Report: {data_source_name}")
    subject = subject_template.format(
        data_source_name=source_info.get("data_source_name", "unknown")
    )
    body = build_email_body(source_info, dq_report)

    msg = MIMEMultipart()
    msg["From"] = email_cfg.get("from_address", "")
    msg["To"] = ", ".join(to_addresses) if isinstance(to_addresses, list) else str(to_addresses)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(email_cfg.get("smtp_host", "localhost"), email_cfg.get("smtp_port", 587)) as server:
            if email_cfg.get("use_tls", True):
                server.starttls()
            username = email_cfg.get("username")
            password = email_cfg.get("password")
            if username and password:
                server.login(username, password)
            server.sendmail(
                email_cfg.get("from_address", ""),
                to_addresses if isinstance(to_addresses, list) else [to_addresses],
                msg.as_string(),
            )
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to send email report: {e}") from e
