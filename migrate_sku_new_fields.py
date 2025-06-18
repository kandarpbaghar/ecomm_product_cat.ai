#!/usr/bin/env python3
"""
Migration script to add new fields to SKU table
"""

from sqlalchemy import text
from database import db
from ai_ecomm import create_app
import sys

def migrate_sku_table():
    """Add new fields to SKU table"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(skus)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            # List of new columns to add
            new_columns = [
                ('taxable', 'BOOLEAN DEFAULT 1'),
                ('inventory_policy', 'VARCHAR(20) DEFAULT "deny"'),
                ('fulfillment_service', 'VARCHAR(50) DEFAULT "manual"'),
                ('requires_shipping', 'BOOLEAN DEFAULT 1')
            ]
            
            # Add each column if it doesn't exist
            for column_name, column_def in new_columns:
                if column_name not in existing_columns:
                    print(f"Adding column: {column_name}")
                    try:
                        db.session.execute(text(f"ALTER TABLE skus ADD COLUMN {column_name} {column_def}"))
                        db.session.commit()
                        print(f"✅ Successfully added column: {column_name}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"❌ Error adding column {column_name}: {e}")
                else:
                    print(f"✓ Column already exists: {column_name}")
            
            # Verify the changes
            print("\n📊 Current SKU table structure:")
            result = db.session.execute(text("PRAGMA table_info(skus)"))
            for row in result:
                print(f"  - {row[1]} ({row[2]})")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    print("🔄 Starting SKU table migration...\n")
    migrate_sku_table()