"""
Shared configuration loading for reports.
"""

import json
import os


def load_reports_config(config_path: str, root_dir: str) -> dict:
    """Load reports config from JSON file."""
    path = config_path if os.path.isabs(config_path) else os.path.join(root_dir, config_path)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)
