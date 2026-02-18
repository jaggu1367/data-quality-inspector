"""
Seeding module: default rules and database seeding logic.
"""

from dq_framework.seeding.default_rules import (
    DEFAULT_RULES,
    seed_data_quality_rules_if_empty,
)

__all__ = ["DEFAULT_RULES", "seed_data_quality_rules_if_empty"]
