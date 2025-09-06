#!/usr/bin/env python3
"""
Database initialization script for Weekly Skate App

This script initializes the database with the required schema and
optionally seeds it with sample data for development.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config, validate_startup_config
from models.database import SCHEMA, db

def init_database(db_path: str = None, force: bool = False):
    """
    Initialize the database with the required schema
    
    Args:
        db_path: Path to database file (uses config default if None)
        force: If True, recreate database even if it exists
    """
    if db_path is None:
        db_path = Config.DB_PATH
    
    # Check if database exists
    db_exists = os.path.exists(db_path)
    
    if db_exists and not force:
        print(f"Database already exists at {db_path}")
        response = input("Do you want to recreate it? (y/N): ")
        if response.lower() != 'y':
            print("Database initialization cancelled")
            return False
    
    # Remove existing database if force is True
    if db_exists and force:
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created database directory: {db_dir}")
    
    # Initialize database with schema
    try:
        with sqlite3.connect(db_path) as conn:
            conn.executescript(SCHEMA)
            
            # Insert default settings
            conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('goalie_phone','')")
            
            conn.commit()
            print(f"Database initialized successfully at {db_path}")
            
            # Verify tables were created
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Created tables: {', '.join(tables)}")
            
            return True
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def seed_development_data(db_path: str = None):
    """
    Seed the database with sample data for development
    
    Args:
        db_path: Path to database file (uses config default if None)
    """
    if db_path is None:
        db_path = Config.DB_PATH
    
    if not os.path.exists(db_path):
        print("Database does not exist. Run init_database first.")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Get current week
            from utils.week_utils import WeekUtils
            iso_year, iso_week = WeekUtils.get_week_key()
            
            # Create current week
            conn.execute(
                "INSERT OR IGNORE INTO weeks(iso_year, iso_week, quota, goalie_notified) VALUES(?,?,?,?)",
                (iso_year, iso_week, 16, 0)
            )
            
            # Get week ID
            week_id = conn.execute(
                "SELECT id FROM weeks WHERE iso_year=? AND iso_week=?",
                (iso_year, iso_week)
            ).fetchone()[0]
            
            # Add sample signups
            sample_signups = [
                ("Alice Johnson", "+15551234567"),
                ("Bob Smith", "+15551234568"),
                ("Charlie Brown", "+15551234569"),
                ("Diana Prince", "+15551234570"),
                ("Eve Adams", "+15551234571"),
                ("Frank Miller", "+15551234572"),
                ("Grace Lee", "+15551234573"),
                ("Henry Wilson", "+15551234574"),
                ("Ivy Chen", "+15551234575"),
                ("Jack Davis", "+15551234576"),
                ("Kate Morgan", "+15551234577"),
                ("Liam O'Connor", "+15551234578"),
                ("Maya Patel", "+15551234579"),
                ("Noah Kim", "+15551234580"),
                ("Olivia Taylor", "+15551234581")
            ]
            
            for name, phone in sample_signups:
                conn.execute(
                    "INSERT OR IGNORE INTO signups(week_id, name, phone, created_at) VALUES(?,?,?,?)",
                    (week_id, name, phone, datetime.utcnow().isoformat())
                )
            
            # Add sample broadcast numbers
            sample_broadcast_numbers = [
                "+15551111111",
                "+15552222222"
            ]
            
            for phone in sample_broadcast_numbers:
                conn.execute(
                    "INSERT OR IGNORE INTO broadcasts(phone) VALUES(?)",
                    (phone,)
                )
            
            # Set sample goalie phone
            conn.execute(
                "UPDATE settings SET value=? WHERE key='goalie_phone'",
                ("+15559999999",)
            )
            
            # Add sample goalie info
            conn.execute(
                "INSERT OR IGNORE INTO goalie_info(phone, venmo_username, created_at, updated_at) VALUES(?,?,?,?)",
                ("+15559999999", "sample-goalie", datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
            )
            
            conn.commit()
            
            # Print summary
            signup_count = conn.execute("SELECT COUNT(*) FROM signups WHERE week_id=?", (week_id,)).fetchone()[0]
            broadcast_count = conn.execute("SELECT COUNT(*) FROM broadcasts").fetchone()[0]
            
            print(f"Development data seeded successfully:")
            print(f"  - Week {iso_week}, {iso_year} created")
            print(f"  - {signup_count} sample signups added")
            print(f"  - {broadcast_count} broadcast numbers added")
            print(f"  - Goalie phone set to +15559999999")
            print(f"  - Sample goalie Venmo username: sample-goalie")
            
            return True
            
    except Exception as e:
        print(f"Error seeding development data: {e}")
        return False

def check_database_health(db_path: str = None):
    """
    Check database health and integrity
    
    Args:
        db_path: Path to database file (uses config default if None)
    """
    if db_path is None:
        db_path = Config.DB_PATH
    
    if not os.path.exists(db_path):
        print(f"Database does not exist at {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Check integrity
            integrity_result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity_result != "ok":
                print(f"Database integrity check failed: {integrity_result}")
                return False
            
            # Check tables exist
            expected_tables = ['weeks', 'signups', 'broadcasts', 'settings', 'goalie_info']
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(expected_tables) - set(existing_tables)
            if missing_tables:
                print(f"Missing tables: {', '.join(missing_tables)}")
                return False
            
            # Check record counts
            for table in expected_tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {table}: {count} records")
            
            print("Database health check passed")
            return True
            
    except Exception as e:
        print(f"Error checking database health: {e}")
        return False

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Weekly Skate database")
    parser.add_argument("--db-path", help="Database file path")
    parser.add_argument("--force", action="store_true", help="Force recreate database")
    parser.add_argument("--seed", action="store_true", help="Seed with development data")
    parser.add_argument("--check", action="store_true", help="Check database health")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Validate configuration
    try:
        validate_startup_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        return 1
    
    db_path = args.db_path or Config.DB_PATH
    
    if args.check:
        success = check_database_health(db_path)
        return 0 if success else 1
    
    # Initialize database
    success = init_database(db_path, args.force)
    if not success:
        return 1
    
    # Seed development data if requested
    if args.seed:
        success = seed_development_data(db_path)
        if not success:
            return 1
    
    print("Database initialization completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
