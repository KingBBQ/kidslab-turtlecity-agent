#!/usr/bin/env python3
"""
Script to sync the player database with data from LMPlayers.dat (FTB Chunks mod).
This imports all historical player data from the NBT file into the local database.
"""

import sys
import os
from datetime import datetime
import database
import nbt_reader
import json

def sync_players_from_nbt():
    """
    Import all players from LMPlayers.dat into the database.
    """
    print("🔄 Synchronizing player database with LMPlayers.dat...")
    print("=" * 60)
    
    try:
        # Load NBT data
        nbt_data = nbt_reader.load_nbt_file(nbt_reader.config.NBT_FILE)
        print(f"✅ Loaded NBT file: {nbt_reader.config.NBT_FILE}")
        
        # Get all players from NBT - Players is a TAG_Compound (dictionary), not a list
        players_dict = nbt_data["Players"]
        
        # Convert to list of player objects
        players = []
        for player_key in players_dict.keys():
            players.append(players_dict[player_key])
        
        total_players = len(players)
        print(f"📊 Found {total_players} players in LMPlayers.dat")
        print()
        
        # Initialize database
        database.initialize_database()
        
        import sqlite3
        conn = sqlite3.connect(database.DATABASE_FILE)
        cursor = conn.cursor()
        
        added_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, player in enumerate(players, 1):
            try:
                username = player["Name"].value
                player_uuid = player["UUID"].value
                
                # Get last seen timestamp
                last_seen_timestamp = player['Stats']['LastSeen'].value
                last_seen_datetime = datetime.fromtimestamp(last_seen_timestamp / 1000)
                last_seen_str = last_seen_datetime.strftime('%Y-%m-%d %H:%M:%S')
                
                # Get joined timestamp (first login)
                joined_timestamp = player['Stats']['Joined'].value
                joined_datetime = datetime.fromtimestamp(joined_timestamp / 1000)
                
                # Get time played (in ticks, convert to minutes)
                time_played_ticks = player['Stats']['TimePlayed'].value
                time_played_minutes = int(time_played_ticks / 20 / 60)  # 20 ticks per second, 60 seconds per minute
                
                # Get time played (in ticks, convert to minutes)
                time_played_ticks = player['Stats']['TimePlayed'].value
                time_played_minutes = int(time_played_ticks / 20 / 60)  # 20 ticks per second, 60 seconds per minute
                
                # Calculate days since last seen
                days_since = (datetime.now() - last_seen_datetime).days
                
                # Get claimed chunks count
                claimed_chunks = nbt_reader.get_claimed_chunks_by_uuid(
                    nbt_reader.config.CLAIMED_JSON, 
                    player_uuid
                )
                chunk_count = len(claimed_chunks) if claimed_chunks else 0
                
                # Check if player exists in database
                cursor.execute('SELECT username, last_login, total_time FROM players WHERE username = ?', (username,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update only if NBT has newer data
                    db_last_login = existing[1]
                    db_total_time = existing[2] or 0
                    
                    if db_last_login is None or last_seen_str > db_last_login:
                        cursor.execute('''
                            UPDATE players
                            SET last_login = ?,
                                last_logout = ?,
                                total_time = ?
                            WHERE username = ?
                        ''', (last_seen_str, last_seen_str, time_played_minutes, username))
                        updated_count += 1
                        print(f"[{i}/{total_players}] 🔄 Updated: {username:<20} (Last: {last_seen_datetime.strftime('%Y-%m-%d')}, {days_since:3d} days, {time_played_minutes:5d} min, {chunk_count:3d} chunks)")
                    else:
                        skipped_count += 1
                        if i % 100 == 0:  # Show progress every 100 players
                            print(f"[{i}/{total_players}] ⏭️  Progress: {skipped_count} skipped (DB newer)...")
                else:
                    # Insert new player
                    cursor.execute('''
                        INSERT INTO players (username, last_login, last_logout, login_count, total_time)
                        VALUES (?, ?, ?, 0, ?)
                    ''', (username, last_seen_str, last_seen_str, time_played_minutes))
                    added_count += 1
                    print(f"[{i}/{total_players}] ✅ Added: {username:<20} (Last: {last_seen_datetime.strftime('%Y-%m-%d')}, {days_since:3d} days, {time_played_minutes:5d} min, {chunk_count:3d} chunks)")
                
            except Exception as e:
                error_count += 1
                print(f"[{i}/{total_players}] ❌ Error processing player: {e}")
        
        conn.commit()
        conn.close()
        
        print()
        print("=" * 60)
        print("📊 Synchronization Summary:")
        print(f"  Total players in NBT: {total_players}")
        print(f"  ✅ Added to database: {added_count}")
        print(f"  🔄 Updated in database: {updated_count}")
        print(f"  ⏭️  Skipped (DB newer): {skipped_count}")
        print(f"  ❌ Errors: {error_count}")
        print()
        
        # Show database stats after sync
        conn = sqlite3.connect(database.DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM players')
        total_in_db = cursor.fetchone()[0]
        conn.close()
        
        print(f"🗄️  Total players in database: {total_in_db}")
        print("✅ Synchronization complete!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: NBT file not found!")
        print(f"   Looking for: {nbt_reader.config.NBT_FILE}")
        print(f"   Make sure the file path in config.py is correct.")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during synchronization: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def show_nbt_vs_database_stats():
    """
    Compare NBT data with database to show what would be synced.
    """
    print("📊 Comparing NBT data with database...")
    print("=" * 60)
    
    try:
        # Load NBT data
        nbt_data = nbt_reader.load_nbt_file(nbt_reader.config.NBT_FILE)
        nbt_players = len(nbt_data["Players"])
        
        # Get database stats
        import sqlite3
        conn = sqlite3.connect(database.DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM players')
        db_players = cursor.fetchone()[0]
        conn.close()
        
        print(f"Players in LMPlayers.dat: {nbt_players}")
        print(f"Players in database: {db_players}")
        print(f"Difference: {nbt_players - db_players}")
        print()
        
        if nbt_players > db_players:
            print(f"ℹ️  Database is missing {nbt_players - db_players} players from NBT file")
            print("   Run with --sync to add them")
        elif nbt_players < db_players:
            print(f"ℹ️  Database has {db_players - nbt_players} more players than NBT file")
            print("   This is normal if players logged in recently")
        else:
            print("✅ Database and NBT file have the same number of players")
        
    except Exception as e:
        print(f"❌ Error comparing data: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sync player database with LMPlayers.dat from FTB Chunks mod'
    )
    parser.add_argument('--sync', action='store_true',
                       help='Sync database with NBT file data')
    parser.add_argument('--stats', action='store_true',
                       help='Show comparison between NBT and database')
    parser.add_argument('--force', action='store_true',
                       help='Force update all players (even if DB is newer)')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        print()
        show_nbt_vs_database_stats()
        return
    
    if args.stats:
        show_nbt_vs_database_stats()
    
    if args.sync:
        if args.force:
            print("⚠️  Warning: --force not yet implemented")
        
        confirmation = input("\n🔄 Start synchronization? This will update the database. (y/N): ")
        if confirmation.lower() == 'y':
            sync_players_from_nbt()
        else:
            print("❌ Synchronization cancelled")

if __name__ == "__main__":
    main()
