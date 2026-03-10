"""
HTML report for data quality validations.

Output directory configured in config/dq_report_config.json.
Uses HTML template from report_templates/dq_report.html when available.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from dq_framework.reports.config import load_reports_config

DEFAULT_TEMPLATE_PATH = "report_templates/dq_report.html"

# CSS and JS for collapsible Validation Details (+ / - toggle with animated magnified box)
_EXPAND_STYLES = """
    .expand-btn { font-size: 1.1em; font-weight: bold; width: 1.8em; height: 1.8em; padding: 0; margin-right: 0.25rem; cursor: pointer; border: 1px solid #ccc; border-radius: 4px; background: #fff; color: #333; line-height: 1; vertical-align: middle; transition: background 0.2s, transform 0.2s; }
    .expand-btn:hover { background: #e8f4fc; transform: scale(1.05); }
    .expand-btn.expanded { background: #e0e0e0; }
    .result-json-wrapper { max-height: 0; overflow: hidden; opacity: 0; transform: scale(0.92); transform-origin: top left; transition: max-height 0.35s ease-out, opacity 0.3s ease, transform 0.35s ease-out; }
    .result-json-wrapper.expanded { max-height: 20em; opacity: 1; transform: scale(1.02); box-shadow: 0 4px 12px rgba(0,0,0,0.12); border-radius: 6px; }
    .result-json { font-size: 0.82em; background: #f8f9fa; padding: 0.6rem; border-radius: 4px; overflow-x: auto; max-height: 18em; overflow-y: auto; margin: 0.35rem 0 0 0; white-space: pre-wrap; word-break: break-word; border: 1px solid #e0e0e0; }
"""

_EXPAND_SCRIPT = """
<script>
function toggleValidationDetail(btn) {
  var wrapper = btn.nextElementSibling;
  if (!wrapper || !wrapper.classList) return;
  var isExpanded = wrapper.classList.contains('expanded');
  if (isExpanded) {
    wrapper.classList.remove('expanded');
    btn.classList.remove('expanded');
    btn.textContent = '+';
    btn.setAttribute('aria-label', 'Expand');
    btn.setAttribute('title', 'Click to expand');
  } else {
    wrapper.classList.add('expanded');
    btn.classList.add('expanded');
    btn.textContent = '-';
    btn.setAttribute('aria-label', 'Collapse');
    btn.setAttribute('title', 'Click to collapse');
  }
}
</script>
"""


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
        <tr><th>Source ID</th><td>{_escape_html(source_info.get('source_id', 'N/A'))}</td></tr>
        <tr><th>Source Type</th><td>{_escape_html(source_info.get('source_type', 'N/A'))}</td></tr>
        <tr><th>Path/Table</th><td>{_escape_html(source_info.get('path_or_table', 'N/A'))}</td></tr>
        <tr><th>Row Count</th><td>{source_info.get('row_count', 0)}</td></tr>
        <tr><th>Columns</th><td>{_escape_html(cols_str)}</td></tr>
        <tr><th>Validation Time</th><td>{_escape_html(source_info.get('timestamp', 'N/A'))}</td></tr>
      </table>
    </section>"""


def _extract_column(rule_result: Dict[str, Any]) -> str:
    """Extract column name(s) from rule expectation_config kwargs."""
    cfg = rule_result.get("expectation_config") or {}
    kwargs = cfg.get("kwargs") or {}
    col = kwargs.get("column")
    if col:
        return str(col)
    col_list = kwargs.get("column_list") or kwargs.get("column_set")
    if col_list and isinstance(col_list, (list, tuple)):
        return ", ".join(str(c) for c in col_list)
    return "N/A"


def _format_value(val: Any) -> str:
    """Format a single value for display (no truncation)."""
    if isinstance(val, (list, tuple)):
        return "[" + ", ".join(_format_value(v) for v in val) + "]"
    if isinstance(val, dict):
        return json.dumps(val, default=str)
    return str(val)


def _format_rule_params(rule_result: Dict[str, Any]) -> str:
    """Format rule kwargs as human-readable string for reports (full values, no shorthand)."""
    cfg = rule_result.get("expectation_config") or {}
    if not cfg and rule_result.get("result") and isinstance(rule_result["result"], dict):
        cfg = rule_result["result"].get("expectation_config") or {}
    kwargs = cfg.get("kwargs") or {}
    if not kwargs:
        return ""
    parts = []
    handled = set()
    # Order: min/max, column, value_set, regex, regex_list, column_set, column_list, type_list, type_, like_pattern
    if "min_value" in kwargs and "max_value" in kwargs:
        parts.append(f"min_value: {kwargs['min_value']}, max_value: {kwargs['max_value']}")
        handled.update(["min_value", "max_value"])
    elif "min_value" in kwargs:
        parts.append(f"min_value: {kwargs['min_value']}")
        handled.add("min_value")
    elif "max_value" in kwargs:
        parts.append(f"max_value: {kwargs['max_value']}")
        handled.add("max_value")
    if "column" in kwargs:
        parts.append(f"column: {kwargs['column']}")
        handled.add("column")
    if "value_set" in kwargs:
        parts.append(f"value_set: {_format_value(kwargs['value_set'])}")
        handled.add("value_set")
    if "regex" in kwargs:
        parts.append(f"regex: {_format_value(kwargs['regex'])}")
        handled.add("regex")
    if "regex_list" in kwargs:
        parts.append(f"regex_list: {_format_value(kwargs['regex_list'])}")
        handled.add("regex_list")
    if "column_set" in kwargs:
        parts.append(f"column_set: {_format_value(kwargs['column_set'])}")
        handled.add("column_set")
    if "column_list" in kwargs:
        parts.append(f"column_list: {_format_value(kwargs['column_list'])}")
        handled.add("column_list")
    if "type_list" in kwargs:
        parts.append(f"type_list: {_format_value(kwargs['type_list'])}")
        handled.add("type_list")
    if "type_" in kwargs:
        parts.append(f"type_: {kwargs['type_']}")
        handled.add("type_")
    if "like_pattern" in kwargs:
        parts.append(f"like_pattern: {_format_value(kwargs['like_pattern'])}")
        handled.add("like_pattern")
    skip = {"catch_exceptions"}
    for k, v in kwargs.items():
        if k not in skip and k not in handled:
            parts.append(f"{k}: {_format_value(v)}")
    return "; ".join(parts) if parts else ""


def _build_layer2_html(dq_report: Dict[str, Any], source_info: Dict[str, Any]) -> str:
    """Data quality report as HTML."""
    summary = dq_report.get("summary", {})
    total = summary.get("total_rules", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    overall = "PASSED" if dq_report.get("success", False) else "FAILED"
    status_class = "status-passed" if overall == "PASSED" else "status-failed"
    source_id = source_info.get("source_id", "N/A")

    PASS_SYMBOL = "&#9989;"   # ✅
    FAIL_SYMBOL = "&#10060;"  # ❌
    rows = []
    for sno, (rule_name, rule_result) in enumerate(dq_report.get("results", {}).items(), 1):
        ok = rule_result.get("success", False)
        symbol = PASS_SYMBOL if ok else FAIL_SYMBOL
        title = "Pass" if ok else "Fail"
        row_class = "pass" if ok else "fail"
        column = _extract_column(rule_result)
        rule_params = _format_rule_params(rule_result)
        # Build Validation Details: full result JSON (same as validation_results.result column)
        # Collapsible with + / - toggle; animated magnified box on expand
        result_json = rule_result.get("result")
        detail_parts = []
        if not ok:
            exc = rule_result.get("exception_info")
            if exc:
                detail_parts.append(_escape_html((exc or "")[:500]))
        if result_json is not None:
            try:
                json_str = json.dumps(result_json, indent=2, default=str)
                detail_parts.append(
                    '<button type="button" class="expand-btn collapsed" onclick="toggleValidationDetail(this)" '
                    'aria-label="Expand" title="Click to expand">+</button>'
                    '<div class="result-json-wrapper collapsed">'
                    f'<pre class="result-json">{_escape_html(json_str)}</pre>'
                    '</div>'
                )
            except (TypeError, ValueError):
                detail_parts.append(_escape_html(str(result_json)[:500]))
        detail = "<br>".join(detail_parts) if detail_parts else ""
        detail_cell = f'<span class="detail">{detail}</span>' if detail else ""
        rule_params_cell = _escape_html(rule_params) if rule_params else ""
        rows.append(
            f"        <tr class=\"{row_class}\">"
            f"<td class=\"sno-cell\">{sno}</td>"
            f"<td>{_escape_html(source_id)}</td>"
            f"<td>{_escape_html(column)}</td>"
            f"<td>{_escape_html(rule_name)}</td>"
            f"<td class=\"status-cell\"><span class=\"status-icon\" title=\"{title}\">{symbol}</span></td>"
            f"<td class=\"rule-params-cell\">{rule_params_cell}</td>"
            f"<td>{detail_cell}</td>"
            f"</tr>"
        )

    rows_html = "\n".join(rows) if rows else "        <tr><td colspan=\"7\">No rules executed.</td></tr>"

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
        <thead><tr><th>Sno</th><th>Source ID</th><th>Column</th><th>DQ Rule</th><th class=\"status-col\">Status</th><th>Rule Details</th><th>Validation Details</th></tr></thead>
        <tbody>
{rows_html}
        </tbody>
      </table>
    </section>"""


def _load_report_template(root_dir: str, template_path: Optional[str] = None) -> Optional[str]:
    """Load HTML template from report_templates. Returns template content or None if not found."""
    path = template_path or DEFAULT_TEMPLATE_PATH
    full_path = path if os.path.isabs(path) else os.path.join(root_dir, path)
    if not os.path.isfile(full_path):
        return None
    with open(full_path, encoding="utf-8") as f:
        return f.read()


def build_html_report(
    source_info: Dict[str, Any],
    dq_report: Dict[str, Any],
    root_dir: Optional[str] = None,
    template_path: Optional[str] = None,
) -> str:
    """Build full HTML report with both layers using template from report_templates."""
    layer1 = _build_layer1_html(source_info)
    layer2 = _build_layer2_html(dq_report, source_info)
    dsn = _escape_html(source_info.get("source_id", "Data Quality Report"))
    page_title = f"Data Quality Report: {dsn}"
    report_title = f"Data Quality Report: {dsn}"
    is_failed = not dq_report.get("success", False)
    failure_banner = ""
    if is_failed:
        failure_banner = """  <div class="overall-failure-banner">
    &#10060; VALIDATION FAILED &mdash; One or more data quality rules did not pass
  </div>
"""

    root = root_dir or os.getcwd()
    template = _load_report_template(root, template_path)
    if template:
        return (
            template.replace("{{page_title}}", page_title)
            .replace("{{report_title}}", report_title)
            .replace("{{failure_banner}}", failure_banner)
            .replace("{{layer1_html}}", layer1)
            .replace("{{layer2_html}}", layer2)
            .replace("{{expand_styles}}", _EXPAND_STYLES)
            .replace("{{expand_script}}", _EXPAND_SCRIPT)
        )

    # Fallback: inline HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
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
    .rules th {{ min-width: 80px; }}
    .rules .sno-cell {{ text-align: center; width: 40px; }}
    .rules .status-col {{ text-align: center; width: 60px; }}
    .rules .status-cell {{ text-align: center; vertical-align: middle; }}
    .status-icon {{ font-size: 1.25em; display: inline-block; }}
    .rules .pass {{ background: #f0fff4; }}
    .rules .pass .status-icon {{ color: #0a7; }}
    .rules .fail {{ background: #fff5f5; }}
    .rules .fail .status-icon {{ color: #c33; }}
    .detail {{ font-size: 0.9em; color: #666; }}
    .rule-params-cell {{ font-size: 0.85em; color: #444; max-width: 220px; }}
    {_EXPAND_STYLES}
  </style>
</head>
<body>
{failure_banner}
  <h1>{report_title}</h1>
{layer1}
{layer2}
{_EXPAND_SCRIPT}
</body>
</html>"""


def write_html_report(
    source_info: Dict[str, Any],
    dq_report: Dict[str, Any],
    output_path: str,
    root_dir: Optional[str] = None,
    template_path: Optional[str] = None,
) -> str:
    """
    Write HTML report to file using template from report_templates.
    Returns the absolute path of the written file.
    """
    html = build_html_report(source_info, dq_report, root_dir, template_path)
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
    Write HTML report if enabled in config. Uses template from report_templates.
    Returns output file path if written, None otherwise.
    """
    root = root_dir or os.getcwd()
    config = load_reports_config(config_path, root)
    html_cfg = config.get("html", {})
    if not html_cfg.get("enabled", False):
        return None

    output_dir = html_cfg.get("output_dir", "html_reports")
    out_path = output_dir if os.path.isabs(output_dir) else os.path.join(root, output_dir)
    template_path = html_cfg.get("template_file", DEFAULT_TEMPLATE_PATH)
    dsn_safe = source_info.get("source_id", "report").replace("/", "_").replace("\\", "_")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{dsn_safe}_{ts}.html"
    full_path = os.path.join(out_path, filename)
    return write_html_report(source_info, dq_report, full_path, root, template_path)
