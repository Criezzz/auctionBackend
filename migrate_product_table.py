#!/usr/bin/env python3
"""
Database migration script to add missing columns to Product table
"""
import pymysql
import os
from app.config import settings

def migrate_product_table():
    """Add missing columns to the product table"""
    
    # Parse database connection details from DATABASE_URL
    # Format: mysql+pymysql://user:password@host:port/database
    database_url = settings.DATABASE_URL
    db_name = database_url.split("/")[-1].split("?")[0]
    base_url = database_url.rsplit("/", 1)[0]
    
    # Parse connection details
    parts = base_url.replace("mysql+pymysql://", "").split("@")
    user_pass = parts[0].split(":")
    host_port = parts[1].split(":")
    
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 3306
    
    print(f"Connecting to MySQL at {host}:{port}...")
    
    try:
        # Connect to database
        connection = pymysql.connect(
            host=host, 
            user=user, 
            password=password, 
            port=port, 
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Check current table structure
            print("Checking current product table structure...")
            cursor.execute("DESCRIBE product")
            columns = cursor.fetchall()
            print("Current columns:")
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']}")
            
            # Check if columns exist
            column_names = [col['Field'] for col in columns]
            
            # Add missing columns
            missing_columns = []
            
            if 'image_url' not in column_names:
                missing_columns.append(('image_url', 'VARCHAR(512) NULL'))
                
            if 'additional_images' not in column_names:
                missing_columns.append(('additional_images', 'TEXT NULL'))
            
            if missing_columns:
                print(f"Adding {len(missing_columns)} missing columns...")
                
                for column_name, column_type in missing_columns:
                    sql = f"ALTER TABLE product ADD COLUMN {column_name} {column_type}"
                    print(f"Executing: {sql}")
                    cursor.execute(sql)
                
                # Commit changes
                connection.commit()
                print("Migration completed successfully!")
                
            else:
                print("All required columns already exist.")
                
                # Verify final structure
                print("Final table structure:")
                cursor.execute("DESCRIBE product")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col['Field']}: {col['Type']}")
        
        connection.close()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_product_table()