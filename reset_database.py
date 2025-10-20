#!/usr/bin/env python3
"""
Script to reset or rebuild the player database.
This script can backup, reset, or completely rebuild the database.
"""

import sqlite3
import os
import shutil
from datetime import datetime
import database

def backup_database():
    """
    Create a backup of the current database.
    """
    if not os.path.exists(database.DATABASE_FILE):
        print("No database file found to backup.")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{database.DATABASE_FILE}.backup_{timestamp}"
    
    try:
        shutil.copy2(database.DATABASE_FILE, backup_file)
        print(f"✅ Database backed up to: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"❌ Error backing up database: {e}")
        return None

def get_database_info():
    """
    Show information about the current database.
    """
    if not os.path.exists(database.DATABASE_FILE):
        print("No database file exists yet.")
        return
    
    try:
        conn = sqlite3.connect(database.DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get total players
        cursor.execute("SELECT COUNT(*) FROM players")
        total = cursor.fetchone()[0]
        
        # Get players with login data
        cursor.execute("SELECT COUNT(*) FROM players WHERE last_login IS NOT NULL")
        with_login = cursor.fetchone()[0]
        
        # Get most recent activity
        cursor.execute("SELECT username, last_login FROM players WHERE last_login IS NOT NULL ORDER BY last_login DESC LIMIT 1")
        recent = cursor.fetchone()
        
        # Get oldest activity
        cursor.execute("SELECT username, last_login FROM players WHERE last_login IS NOT NULL ORDER BY last_login ASC LIMIT 1")
        oldest = cursor.fetchone()
        
        print("\n📊 Database Information:")
        print("=" * 60)
        print(f"Database file: {database.DATABASE_FILE}")
        print(f"File size: {os.path.getsize(database.DATABASE_FILE) / 1024:.2f} KB")
        print(f"Total players: {total}")
        print(f"Players with login data: {with_login}")
        
        if recent:
            print(f"Most recent activity: {recent[0]} ({recent[1]})")
        if oldest:
            print(f"Oldest activity: {oldest[0]} ({oldest[1]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

def reset_database():
    """
    Delete the database and create a fresh one.
    """
    print("\n⚠️  WARNING: This will delete all player data!")
    
    # Show current database info
    get_database_info()
    
    # Ask for confirmation
    confirmation = input("\nAre you sure you want to reset the database? (type 'YES' to confirm): ")
    if confirmation != 'YES':
        print("❌ Reset cancelled.")
        return False
    
    # Backup first
    backup_file = backup_database()
    if not backup_file:
        proceed = input("Backup failed. Continue anyway? (y/N): ")
        if proceed.lower() != 'y':
            print("❌ Reset cancelled.")
            return False
    
    # Delete database
    try:
        if os.path.exists(database.DATABASE_FILE):
            os.remove(database.DATABASE_FILE)
            print(f"✅ Database deleted: {database.DATABASE_FILE}")
        
        # Create fresh database
        database.initialize_database()
        print(f"✅ Fresh database created: {database.DATABASE_FILE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def vacuum_database():
    """
    Optimize database by running VACUUM.
    This reclaims unused space and optimizes the database file.
    """
    if not os.path.exists(database.DATABASE_FILE):
        print("No database file exists yet.")
        return
    
    try:
        conn = sqlite3.connect(database.DATABASE_FILE)
        print("Running VACUUM to optimize database...")
        conn.execute("VACUUM")
        conn.close()
        print("✅ Database optimized successfully")
    except Exception as e:
        print(f"❌ Error optimizing database: {e}")

def show_top_players(limit=10):
    """
    Show top players by total time or login count.
    """
    if not os.path.exists(database.DATABASE_FILE):
        print("No database file exists yet.")
        return
    
    try:
        conn = sqlite3.connect(database.DATABASE_FILE)
        cursor = conn.cursor()
        
        print(f"\n🏆 Top {limit} Players by Total Time:")
        print("=" * 70)
        cursor.execute('''
            SELECT username, total_time, login_count, last_login
            FROM players
            ORDER BY total_time DESC
            LIMIT ?
        ''', (limit,))
        
        print(f"{'Rank':<6} {'Username':<20} {'Time (min)':<12} {'Logins':<8} {'Last Login':<20}")
        print("-" * 70)
        
        for idx, row in enumerate(cursor.fetchall(), 1):
            username, total_time, login_count, last_login = row
            last_login_str = last_login if last_login else "Never"
            print(f"{idx:<6} {username:<20} {total_time:<12} {login_count:<8} {last_login_str:<20}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing top players: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management tool for player data')
    parser.add_argument('--info', action='store_true', 
                       help='Show database information')
    parser.add_argument('--backup', action='store_true',
                       help='Create a backup of the database')
    parser.add_argument('--reset', action='store_true',
                       help='Reset the database (WARNING: deletes all data)')
    parser.add_argument('--vacuum', action='store_true',
                       help='Optimize database file')
    parser.add_argument('--top', type=int, metavar='N',
                       help='Show top N players by total time')
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n")
        get_database_info()
        return
    
    if args.info:
        get_database_info()
    
    if args.backup:
        backup_database()
    
    if args.top:
        show_top_players(args.top)
    
    if args.vacuum:
        vacuum_database()
    
    if args.reset:
        reset_database()

if __name__ == "__main__":
    main()
