# Report Templates

HTML reports are generated using the template in this folder.

## Template: `dq_report.html`

Standard HTML template for Data Quality reports. Uses the same structure and styling as the built-in fallback to ensure reports look identical.

### Placeholders

| Placeholder       | Description                                        |
|-------------------|----------------------------------------------------|
| `{{page_title}}`  | Browser tab title (e.g. "Data Quality Report: customers_csv") |
| `{{report_title}}`| Main H1 heading text                              |
| `{{failure_banner}}` | Red banner shown when validation fails (empty when passed) |
| `{{layer1_html}}`| Input data source section (name, type, rows, columns, etc.) |
| `{{layer2_html}}`| Data quality report section (summary + per-rule results) |

### Customization

Edit `dq_report.html` to change layout, styling, or structure. The placeholders must remain for the report generator to populate content.

To use a different template file, set `template_file` in `config/dq_report_config.json` under the `html` section:

```json
{
  "html": {
    "enabled": true,
    "output_dir": "html_reports",
    "template_file": "report_templates/dq_report.html"
  }
}
```
