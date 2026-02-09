"""
Seed data_quality_rules by reading rules from JSON files per dataset.
Rules are stored in rules/{dataset_name}.json files and are marked as active.
Run with: python scripts/seed_comprehensive_rules.py
"""
import sys
import os
import json
import glob

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dq_framework.database import db_manager, DataQualityRule


def load_rules_from_json(rules_dir: str) -> dict:
    """
    Load rules from JSON files in the rules directory.
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


def get_all_rules(rules_dir: str = "rules") -> list:
    """
    Load all rules from JSON files and return as a flat list.
    """
    rules_by_dataset = load_rules_from_json(rules_dir)
    all_rules = []
    
    for dataset_name, rules in rules_by_dataset.items():
        for rule in rules:
            # Ensure dataset_name is set (use filename if not in JSON)
            if "dataset_name" not in rule:
                rule["dataset_name"] = dataset_name
            all_rules.append(rule)
    
    return all_rules


def seed_comprehensive_rules(replace_existing: bool = True, rules_dir: str = "rules"):
    """
    Seed rules from JSON files. If replace_existing, clears all first. 
    Otherwise upserts: update if same rule_name+dataset exists.
    """
    # Load rules from JSON files
    all_rules = get_all_rules(rules_dir)
    
    if not all_rules:
        print("  No rules found in JSON files. Nothing to seed.")
        return
    
    session = db_manager.get_session()
    try:
        if replace_existing:
            deleted = session.query(DataQualityRule).delete()
            session.commit()
            print(f"  Cleared {deleted} existing rules.")

        added = 0
        updated = 0
        for r in all_rules:
            existing = session.query(DataQualityRule).filter(
                DataQualityRule.rule_name == r["rule_name"],
                DataQualityRule.dataset_name == r["dataset_name"],
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
                    dataset_name=r["dataset_name"],
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
    print("Seeding data quality rules from JSON files...")
    db_manager.create_tables()
    seed_comprehensive_rules(replace_existing=True)
    print("Done. Run: python scripts/run_expectations.py --save-results")


if __name__ == "__main__":
    main()
