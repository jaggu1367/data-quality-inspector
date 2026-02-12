"""
HTML report for data quality validations.
Two layers: (1) Input data source details, (2) Data quality report.
Output directory configured in config/dq_report_config.json.
"""
import os
from datetime import datetime
from typing import Any, Dict, Optional

from dq_framework.email_report import load_reports_config


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_layer1_html(source_info: Dict[str, Any]) -> str:
    """Input data source details as HTML."""
    cols = source_info.get("columns", [])
    cols_str = ", ".join(str(c) for c in cols) if cols else "N/A"
    return f"""
    <section class="layer">
      <h2>Input Data Source</h2>
      <table>
        <tr><th>Data Source Name</th><td>{_escape_html(source_info.get('data_source_name', 'N/A'))}</td></tr>
        <tr><th>Source Type</th><td>{_escape_html(source_info.get('source_type', 'N/A'))}</td></tr>
        <tr><th>Path/Table</th><td>{_escape_html(source_info.get('path_or_table', 'N/A'))}</td></tr>
        <tr><th>Row Count</th><td>{source_info.get('row_count', 0)}</td></tr>
        <tr><th>Columns</th><td>{_escape_html(cols_str)}</td></tr>
        <tr><th>Validation Time</th><td>{_escape_html(source_info.get('timestamp', 'N/A'))}</td></tr>
      </table>
    </section>"""


def _build_layer2_html(dq_report: Dict[str, Any]) -> str:
    """Data quality report as HTML."""
    summary = dq_report.get("summary", {})
    total = summary.get("total_rules", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    overall = "PASSED" if dq_report.get("success", False) else "FAILED"
    status_class = "status-passed" if overall == "PASSED" else "status-failed"

    PASS_SYMBOL = "&#9989;"   # ✅
    FAIL_SYMBOL = "&#10060;"  # ❌
    rows = []
    for rule_name, rule_result in dq_report.get("results", {}).items():
        ok = rule_result.get("success", False)
        symbol = PASS_SYMBOL if ok else FAIL_SYMBOL
        title = "Pass" if ok else "Fail"
        row_class = "pass" if ok else "fail"
        detail = ""
        if not ok:
            exc = rule_result.get("exception_info")
            if exc:
                detail = _escape_html((exc or "")[:200])
            else:
                res = rule_result.get("result") or {}
                inner = res.get("result") if isinstance(res, dict) else res
                if isinstance(inner, dict) and "unexpected_count" in inner:
                    detail = f"Unexpected count: {inner['unexpected_count']}"
        detail_cell = f'<span class="detail">{_escape_html(detail)}</span>' if detail else ""
        rows.append(f"        <tr class=\"{row_class}\"><td class=\"status-cell\"><span class=\"status-icon\" title=\"{title}\">{symbol}</span></td><td>{_escape_html(rule_name)}</td><td>{detail_cell}</td></tr>")

    rows_html = "\n".join(rows) if rows else "        <tr><td colspan=\"3\">No rules executed.</td></tr>"

    return f"""
    <section class="layer">
      <h2>Data Quality Report</h2>
      <table class="summary">
        <tr><th>Overall Status</th><td class=\"{status_class}\">{overall}</td></tr>
        <tr><th>Total Rules</th><td>{total}</td></tr>
        <tr><th>Passed</th><td>{passed}</td></tr>
        <tr><th>Failed</th><td>{failed}</td></tr>
      </table>
      <h3>Per-rule results</h3>
      <table class="rules">
        <thead><tr><th class=\"status-col\">Status</th><th>Rule</th><th>Details</th></tr></thead>
        <tbody>
{rows_html}
        </tbody>
      </table>
    </section>"""


def build_html_report(source_info: Dict[str, Any], dq_report: Dict[str, Any]) -> str:
    """Build full HTML report with both layers."""
    layer1 = _build_layer1_html(source_info)
    layer2 = _build_layer2_html(dq_report)
    dsn = _escape_html(source_info.get("data_source_name", "Data Quality Report"))
    is_failed = not dq_report.get("success", False)
    failure_banner = ""
    if is_failed:
        failure_banner = """
  <div class="overall-failure-banner">
    &#10060; VALIDATION FAILED &mdash; One or more data quality rules did not pass
  </div>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Data Quality Report: {dsn}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 2rem; max-width: 900px; }}
    .overall-failure-banner {{ background: #c33; color: white; font-weight: 700; font-size: 1.1rem; padding: 1rem 1.25rem; margin-bottom: 1.5rem; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.15); }}
    h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 0.5rem; }}
    h2 {{ color: #16213e; font-size: 1.1rem; margin-top: 1.5rem; }}
    h3 {{ color: #0f3460; font-size: 1rem; margin-top: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.5rem 0; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background: #eee; font-weight: 600; width: 140px; }}
    .layer {{ margin-bottom: 2rem; }}
    .summary th {{ width: 140px; }}
    .status-passed {{ color: #0a7; font-weight: 600; }}
    .status-failed {{ color: #c33; font-weight: 600; }}
    .rules th {{ width: 60px; }}
    .rules .status-col {{ text-align: center; }}
    .rules .status-cell {{ text-align: center; vertical-align: middle; }}
    .status-icon {{ font-size: 1.25em; display: inline-block; }}
    .rules .pass {{ background: #f0fff4; }}
    .rules .pass .status-icon {{ color: #0a7; }}
    .rules .fail {{ background: #fff5f5; }}
    .rules .fail .status-icon {{ color: #c33; }}
    .detail {{ font-size: 0.9em; color: #666; }}
  </style>
</head>
<body>
{failure_banner}
  <h1>Data Quality Report: {dsn}</h1>
{layer1}
{layer2}
</body>
</html>"""


def write_html_report(
    source_info: Dict[str, Any],
    dq_report: Dict[str, Any],
    output_path: str,
) -> str:
    """
    Write HTML report to file. Returns the absolute path of the written file.
    """
    html = build_html_report(source_info, dq_report)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(output_path)


def maybe_write_html_report(
    source_info: Dict[str, Any],
    dq_report: Dict[str, Any],
    config_path: str = "config/dq_report_config.json",
    root_dir: Optional[str] = None,
) -> Optional[str]:
    """
    Write HTML report if enabled in config. Returns output file path if written, None otherwise.
    """
    root = root_dir or os.getcwd()
    config = load_reports_config(config_path, root)
    html_cfg = config.get("html", {})
    if not html_cfg.get("enabled", False):
        return None

    output_dir = html_cfg.get("output_dir", "html_reports")
    out_path = output_dir if os.path.isabs(output_dir) else os.path.join(root, output_dir)
    dsn_safe = source_info.get("data_source_name", "report").replace("/", "_").replace("\\", "_")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{dsn_safe}_{ts}.html"
    full_path = os.path.join(out_path, filename)
    return write_html_report(source_info, dq_report, full_path)
