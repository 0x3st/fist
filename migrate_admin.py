#!/usr/bin/env python3
"""
Database migration script to create admin table and migrate admin credentials.

This script:
1. Creates the admin table if it doesn't exist
2. Migrates the current admin credentials from config to database
3. Uses secure password hashing (bcrypt via passlib)
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import Base, Admin
from auth import get_password_hash
from database import DatabaseOperations


def migrate_admin_credentials():
    """Migrate admin credentials from config to database."""
    print("Starting admin credentials migration...")
    
    # Create database engine and session
    engine = create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables (including the new admin table)
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if admin already exists in database
        existing_admin = DatabaseOperations.get_admin_by_username(db, Config.ADMIN_USERNAME)
        
        if existing_admin:
            print(f"Admin '{Config.ADMIN_USERNAME}' already exists in database. Skipping migration.")
        else:
            # Hash the admin password from config
            password_hash = get_password_hash(Config.ADMIN_PASSWORD)
            
            # Create admin in database
            admin = DatabaseOperations.create_admin(db, Config.ADMIN_USERNAME, password_hash)
            print(f"Successfully migrated admin '{Config.ADMIN_USERNAME}' to database.")
            print(f"Admin ID: {admin.admin_id}")
            
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_admin_credentials()
