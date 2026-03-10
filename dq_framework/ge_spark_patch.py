"""
Monkeypatch for Great Expectations Spark drop() bug.

GE 1.11.3 uses df.drop(F.col("__unexpected")) in Spark map-metric code.
PySpark's drop() expects a column name string, not a Column object, causing:
  py4j.Py4JException: Method drop([class org.apache.spark.sql.Column, ...]) does not exist

This module patches the GE source files to use drop("__unexpected") instead.
Call apply_ge_spark_patch() before any GE validation when using Spark engine.
"""

from __future__ import annotations

import os
from pathlib import Path


def _get_ge_base_path() -> Path | None:
    """Return the base path of the installed great_expectations package."""
    try:
        import importlib.util

        spec = importlib.util.find_spec("great_expectations")
        if spec and spec.origin:
            return Path(spec.origin).parent
    except (ImportError, ValueError, AttributeError):
        pass
    return None


def _patch_file(file_path: Path, old: str, new: str) -> bool:
    """Replace old with new in file. Returns True if file was modified."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if old in content:
            file_path.write_text(content.replace(old, new), encoding="utf-8")
            return True
    except (OSError, UnicodeDecodeError):
        pass
    return False


def apply_ge_spark_patch() -> bool:
    """
    Patch Great Expectations Spark map-metric code to fix the drop() bug.

    Replaces .drop(F.col("__unexpected")) with .drop("__unexpected") in all
    affected GE modules. Safe to call multiple times (idempotent after first run).

    Returns True if any file was patched, False otherwise.
    """
    base = _get_ge_base_path()
    if base is None:
        return False

    mp = base / "expectations" / "metrics" / "map_metric_provider"
    if not mp.exists():
        return False

    # The bug: drop() receives F.col("__unexpected") but PySpark expects a string
    # GE uses multiline: .drop(  # noqa: E712 ...\n        F.col("__unexpected")\n    )
    old_pattern = '.drop(  # noqa: E712 # FIXME CoP\n        F.col("__unexpected")\n    )'
    new_pattern = '.drop("__unexpected")'

    files_to_patch = [
        mp / "column_map_condition_auxilliary_methods.py",
        mp / "multicolumn_map_condition_auxilliary_methods.py",
        mp / "map_condition_auxilliary_methods.py",
        mp / "column_pair_map_condition_auxilliary_methods.py",
    ]

    modified = False
    for fp in files_to_patch:
        if fp.exists() and _patch_file(fp, old_pattern, new_pattern):
            modified = True

    return modified
