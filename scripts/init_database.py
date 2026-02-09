"""
Database initialization script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dq_framework.database import db_manager

if __name__ == '__main__':
    print("Initializing database tables...")
    try:
        db_manager.create_tables()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)
