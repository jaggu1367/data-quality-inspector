"""
Seed data_quality_rules by reading rules from JSON files in the rules folder.
Loads rules from rules/{dataset_name}.json and seeds them into the database.
Run with: python scripts/seed_dq_rules.py
"""
import sys
import os
import json
import glob

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dq_framework.database import db_manager, DataQualityRule

DEFAULT_SOURCES_CONFIG = "config/data_sources.json"


def get_dataset_names_from_sources(config_path: str) -> set[str] | None:
    """Extract unique rules_table names (for rules files). Uses rules_table if present, else source_id."""
    path = config_path if os.path.isabs(config_path) else os.path.join(_root, config_path)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    sources = config.get("sources", [])
    if isinstance(sources, dict):
        sources = list(sources.values())
    result = set()
    for s in sources:
        if not isinstance(s, dict):
            continue
        name = s.get("rules_table") or s.get("source_id")
        if name:
            result.add(name)
    return result or None


def load_rules_from_json(rules_dir: str, dataset_names_filter: set[str] | None = None) -> dict:
    """
    Load rules from JSON files in the rules directory.
    If dataset_names_filter is set, only load rules for those dataset_names.
    Returns a dictionary mapping dataset_name to list of rules.
    """
    rules_by_dataset = {}
    rules_path = os.path.join(_root, rules_dir)
    
    if not os.path.exists(rules_path):
        print(f"Warning: Rules directory '{rules_path}' does not exist.")
        return rules_by_dataset
    
    # Find all JSON files in the rules directory
    json_files = glob.glob(os.path.join(rules_path, "*.json"))
    
    for json_file in json_files:
        dataset_name = os.path.splitext(os.path.basename(json_file))[0]
        if dataset_names_filter is not None and dataset_name not in dataset_names_filter:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                if isinstance(rules, list):
                    rules_by_dataset[dataset_name] = rules
                    print(f"  Loaded {len(rules)} rules from {dataset_name}.json")
                else:
                    print(f"  Warning: {json_file} does not contain a list of rules")
        except json.JSONDecodeError as e:
            print(f"  Error: Invalid JSON in {json_file}: {e}")
        except Exception as e:
            print(f"  Error reading {json_file}: {e}")
    
    return rules_by_dataset


def get_all_rules(rules_dir: str = "rules", dataset_names_filter: set[str] | None = None) -> list:
    """
    Load all rules from JSON files and return as a flat list.
    If dataset_names_filter is set, only load rules for those dataset_names.
    """
    rules_by_dataset = load_rules_from_json(rules_dir, dataset_names_filter)
    all_rules = []
    
    for dataset_name, rules in rules_by_dataset.items():
        for rule in rules:
            # Ensure rules_table_name is set (support both keys for backward compat)
            rules_table = rule.get("rules_table_name") or rule.get("data_source_name") or dataset_name
            rule["rules_table_name"] = rules_table
            all_rules.append(rule)
    
    return all_rules


def seed_dq_rules(
    replace_existing: bool = True,
    rules_dir: str = "rules",
    sources_config: str = DEFAULT_SOURCES_CONFIG,
    use_sources_filter: bool = True,
    rules_table_filter: set[str] | None = None,
):
    """
    Seed rules from JSON files. If replace_existing, clears rules first (all, or only
    those matching rules_table_filter when provided). Otherwise upserts.
    rules_table_filter: when set, only load and seed rules for these rules_table names.
    """
    if rules_table_filter:
        dataset_names = rules_table_filter
        use_sources_filter = False
    else:
        dataset_names = get_dataset_names_from_sources(sources_config) if use_sources_filter else None
    all_rules = get_all_rules(rules_dir, dataset_names)

    if not all_rules:
        print("  No rules found in JSON files. Nothing to seed.")
        return

    session = db_manager.get_session()
    try:
        if replace_existing:
            if rules_table_filter:
                deleted = session.query(DataQualityRule).filter(
                    DataQualityRule.rules_table_name.in_(rules_table_filter)
                ).delete(synchronize_session=False)
                session.commit()
                print(f"  Cleared {deleted} existing rules for {rules_table_filter}.")
            else:
                deleted = session.query(DataQualityRule).delete()
                session.commit()
                print(f"  Cleared {deleted} existing rules.")

        added = 0
        updated = 0
        for r in all_rules:
            existing = session.query(DataQualityRule).filter(
                DataQualityRule.rule_name == r["rule_name"],
                DataQualityRule.rules_table_name == r["rules_table_name"],
            ).first()
            if existing:
                existing.expectation_type = r["expectation_type"]
                existing.kwargs = r["kwargs"]
                existing.column_name = r.get("column_name")
                existing.description = r.get("description")
                existing.is_active = True
                updated += 1
            else:
                rule = DataQualityRule(
                    rule_name=r["rule_name"],
                    expectation_type=r["expectation_type"],
                    kwargs=r["kwargs"],
                    rules_table_name=r["rules_table_name"],
                    column_name=r.get("column_name"),
                    description=r.get("description"),
                    is_active=True,
                )
                session.add(rule)
                added += 1
        session.commit()
        total = session.query(DataQualityRule).count()
        print(f"  Added {added}, updated {updated} rules. Total: {total} active rules.")
    finally:
        session.close()


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Seed data_quality_rules from rules/*.json")
    ap.add_argument("--source-id", "-s", help="Only seed rules for this source ID from config/data_sources.json")
    ap.add_argument("--sources-config", default=DEFAULT_SOURCES_CONFIG, help="Path to data sources config")
    a = ap.parse_args()
    print("Seeding data quality rules from JSON files...")
    db_manager.create_tables()
    rules_filter = None
    if a.source_id:
        path = a.sources_config if os.path.isabs(a.sources_config) else os.path.join(_root, a.sources_config)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            for s in cfg.get("sources", []):
                if isinstance(s, dict) and s.get("source_id") == a.source_id:
                    rules_filter = {s.get("rules_table") or s.get("source_id")}
                    break
        if not rules_filter:
            print(f"  Warning: source_id '{a.source_id}' not found in config. Seeding all.")
    seed_dq_rules(
        replace_existing=True,
        sources_config=a.sources_config,
        rules_table_filter=rules_filter,
    )
    print("Done.")


if __name__ == "__main__":
    main()
