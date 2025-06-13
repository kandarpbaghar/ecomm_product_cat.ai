#!/usr/bin/env python3
"""
Database migration script to add missing Shopify fields to SKU models.
This script adds all the missing columns identified in the Shopify comparison.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from sqlalchemy import text

def run_migration():
    """Run the database migration to add missing Shopify fields"""
    print("Starting SKU model migration...")
    
    # Check if we're in a Flask app context
    try:
        from flask import current_app
        if not current_app:
            print("Error: No Flask app context found. Please run this from within the Flask application.")
            return False
    except RuntimeError:
        print("Error: No Flask app context found. Please run this from within the Flask application.")
        return False
    
    try:
        # Migration queries - only add columns if they don't exist
        migration_queries = [
            # SKU table updates
            """
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='skus' AND sql LIKE '%template_suffix%'
            """,
            """
            ALTER TABLE skus ADD COLUMN template_suffix VARCHAR(255)
            """,
            """
            ALTER TABLE skus ADD COLUMN published_scope VARCHAR(50) DEFAULT 'web'
            """,
            """
            ALTER TABLE skus ADD COLUMN admin_graphql_api_id VARCHAR(255)
            """,
            
            # SKU variants table updates  
            """
            ALTER TABLE sku_variants ADD COLUMN inventory_policy VARCHAR(50) DEFAULT 'deny'
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN fulfillment_service VARCHAR(50) DEFAULT 'manual'
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN taxable BOOLEAN DEFAULT 1
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN grams INTEGER
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN image_id VARCHAR(50)
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN inventory_item_id VARCHAR(50)
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN old_inventory_quantity INTEGER
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN requires_shipping BOOLEAN DEFAULT 1
            """,
            """
            ALTER TABLE sku_variants ADD COLUMN admin_graphql_api_id VARCHAR(255)
            """,
            
            # SKU images table updates
            """
            ALTER TABLE sku_images ADD COLUMN variant_ids TEXT
            """,
            """
            ALTER TABLE sku_images ADD COLUMN admin_graphql_api_id VARCHAR(255)
            """,
            
            # Create product_options table
            """
            CREATE TABLE IF NOT EXISTS product_options (
                id INTEGER PRIMARY KEY,
                sku_id INTEGER NOT NULL,
                shopify_id VARCHAR(50) UNIQUE,
                name VARCHAR(255) NOT NULL,
                position INTEGER DEFAULT 0,
                values TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sku_id) REFERENCES skus(id)
            )
            """
        ]
        
        # Helper function to check if column exists
        def column_exists(table_name, column_name):
            result = db.session.execute(text(f"""
                PRAGMA table_info({table_name})
            """)).fetchall()
            return any(col[1] == column_name for col in result)
        
        # Helper function to check if table exists
        def table_exists(table_name):
            result = db.session.execute(text(f"""
                SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'
            """)).fetchone()
            return result is not None
        
        # Execute migrations
        migration_count = 0
        
        # SKU table migrations
        print("Updating skus table...")
        if not column_exists('skus', 'template_suffix'):
            db.session.execute(text("ALTER TABLE skus ADD COLUMN template_suffix VARCHAR(255)"))
            migration_count += 1
            print("  ✓ Added template_suffix column")
        else:
            print("  - template_suffix column already exists")
            
        if not column_exists('skus', 'published_scope'):
            db.session.execute(text("ALTER TABLE skus ADD COLUMN published_scope VARCHAR(50) DEFAULT 'web'"))
            migration_count += 1
            print("  ✓ Added published_scope column")
        else:
            print("  - published_scope column already exists")
            
        if not column_exists('skus', 'admin_graphql_api_id'):
            db.session.execute(text("ALTER TABLE skus ADD COLUMN admin_graphql_api_id VARCHAR(255)"))
            migration_count += 1
            print("  ✓ Added admin_graphql_api_id column")
        else:
            print("  - admin_graphql_api_id column already exists")
        
        # SKU variants table migrations
        print("Updating sku_variants table...")
        variant_columns = [
            ('inventory_policy', 'VARCHAR(50) DEFAULT "deny"'),
            ('fulfillment_service', 'VARCHAR(50) DEFAULT "manual"'),
            ('taxable', 'BOOLEAN DEFAULT 1'),
            ('grams', 'INTEGER'),
            ('image_id', 'VARCHAR(50)'),
            ('inventory_item_id', 'VARCHAR(50)'),
            ('old_inventory_quantity', 'INTEGER'),
            ('requires_shipping', 'BOOLEAN DEFAULT 1'),
            ('admin_graphql_api_id', 'VARCHAR(255)')
        ]
        
        for column_name, column_def in variant_columns:
            if not column_exists('sku_variants', column_name):
                db.session.execute(text(f"ALTER TABLE sku_variants ADD COLUMN {column_name} {column_def}"))
                migration_count += 1
                print(f"  ✓ Added {column_name} column")
            else:
                print(f"  - {column_name} column already exists")
        
        # SKU images table migrations
        print("Updating sku_images table...")
        if not column_exists('sku_images', 'variant_ids'):
            db.session.execute(text("ALTER TABLE sku_images ADD COLUMN variant_ids TEXT"))
            migration_count += 1
            print("  ✓ Added variant_ids column")
        else:
            print("  - variant_ids column already exists")
            
        if not column_exists('sku_images', 'admin_graphql_api_id'):
            db.session.execute(text("ALTER TABLE sku_images ADD COLUMN admin_graphql_api_id VARCHAR(255)"))
            migration_count += 1
            print("  ✓ Added admin_graphql_api_id column")
        else:
            print("  - admin_graphql_api_id column already exists")
        
        # Create product_options table
        print("Creating product_options table...")
        if not table_exists('product_options'):
            db.session.execute(text("""
                CREATE TABLE product_options (
                    id INTEGER PRIMARY KEY,
                    sku_id INTEGER NOT NULL,
                    shopify_id VARCHAR(50) UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    position INTEGER DEFAULT 0,
                    values TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sku_id) REFERENCES skus(id)
                )
            """))
            migration_count += 1
            print("  ✓ Created product_options table")
        else:
            print("  - product_options table already exists")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\nMigration completed successfully!")
        print(f"Applied {migration_count} changes.")
        print("SKU models now include all Shopify product fields.")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    # This can be run standalone if needed
    print("This migration script should be run from within the Flask application context.")
    print("Use: python -c 'from migrate_sku_fields import run_migration; run_migration()'")