#!/usr/bin/env python3
"""
Script to find inactive players and generate unclaim commands.
This script finds players who haven't logged in for more than the specified number of days
and generates /admin unclaim_all commands for each of them.
"""

import sqlite3
import argparse
import time
from datetime import datetime, timedelta
from database import DATABASE_FILE
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Try to import RCON dependencies
try:
    from mcrcon import MCRcon
    import config
    RCON_AVAILABLE = True
except ImportError:
    RCON_AVAILABLE = False

# Try to import NBT reader for chunk checking
try:
    import nbt_reader
    CHUNK_CHECK_AVAILABLE = True
except Exception as e:
    CHUNK_CHECK_AVAILABLE = False
    print(f"Warning: Chunk checking not available: {e}")
    print("Will proceed without chunk verification.")

def check_player_has_chunks(username):
    """
    Check if a player has any claimed chunks.
    
    Args:
        username (str): The player's username
        
    Returns:
        tuple: (has_chunks: bool, chunk_count: int, chunk_list: list)
    """
    if not CHUNK_CHECK_AVAILABLE:
        print(f"Warning: Cannot check chunks for {username} - NBT reader not available")
        # If we can't check, assume they might have chunks to be safe
        return True, -1, []
    
    try:
        last_seen_datetime, days_since_last_seen, claimed_chunks = nbt_reader.getPlayerStats(username)
        if claimed_chunks:
            return True, len(claimed_chunks), claimed_chunks
        else:
            return False, 0, []
    except Exception as e:
        print(f"Warning: Could not check chunks for {username}: {e}")
        # If we can't check, assume they might have chunks to be safe
        return True, -1, []

def get_inactive_players(days=180):
    """
    Get players who haven't logged in for more than the specified number of days.
    
    Args:
        days (int): Number of days of inactivity (default: 180)
        
    Returns:
        list: List of tuples containing (username, last_login, days_inactive)
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Exclude known admin/staff users from unclaim operations
    excluded_users = ['MatzE_', 'KingBBQ42', '<KingBBQ42>', 'Layre']
    excluded_placeholders = ','.join(['?' for _ in excluded_users])
    
    # Find players who haven't logged in since the cutoff date, excluding staff
    cursor.execute(f'''
        SELECT username, last_login, login_count, total_time
        FROM players
        WHERE (last_login < ? OR last_login IS NULL)
        AND username NOT IN ({excluded_placeholders})
        ORDER BY last_login ASC
    ''', (cutoff_date_str, *excluded_users))
    
    inactive_players = []
    for row in cursor.fetchall():
        username, last_login, login_count, total_time = row
        
        if last_login:
            last_login_date = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S')
            days_inactive = (datetime.now() - last_login_date).days
        else:
            days_inactive = "Never logged in"
            
        inactive_players.append((username, last_login, days_inactive))
    
    conn.close()
    return inactive_players

def generate_unclaim_commands(inactive_players, output_file=None, check_chunks=True):
    """
    Generate /admin unclaim_all commands for inactive players.
    
    Args:
        inactive_players (list): List of inactive player tuples
        output_file (str, optional): File to write commands to. If None, prints to console.
        check_chunks (bool): Whether to check if players actually have chunks before generating commands
    """
    commands = []
    skipped_players = []
    
    for username, last_login, days_inactive in inactive_players:
        if check_chunks:
            has_chunks, chunk_count, chunk_list = check_player_has_chunks(username)
            if not has_chunks and chunk_count == 0:
                skipped_players.append((username, "No chunks claimed"))
                continue
            elif chunk_count == -1:
                print(f"Warning: Could not verify chunks for {username}, including command anyway")
            elif chunk_count > 0:
                print(f"Player {username} has {chunk_count} claimed chunks")
        
        command = f"/admin unclaim_all {username}"
        commands.append(command)
    
    if skipped_players:
        print(f"\nSkipped {len(skipped_players)} players with no claimed chunks:")
        for username, reason in skipped_players:
            print(f"  - {username}: {reason}")
    
    if output_file:
        with open(output_file, 'w') as f:
            for command in commands:
                f.write(command + '\n')
        print(f"Commands written to {output_file}")
    else:
        for command in commands:
            print(command)
    
    return commands

def execute_unclaim_commands_via_rcon(inactive_players, batch_size=5, delay_between_batches=2, check_chunks=True):
    """
    Execute unclaim commands directly via RCON.
    
    Args:
        inactive_players (list): List of inactive player tuples
        batch_size (int): Number of commands to send per batch
        delay_between_batches (float): Delay in seconds between batches
        check_chunks (bool): Whether to check if players actually have chunks before executing commands
        
    Returns:
        tuple: (executed_count, skipped_count, errors)
    """
    if not RCON_AVAILABLE:
        print("Error: RCON not available. Make sure 'mcrcon' is installed and config.py exists with RCON settings")
        return 0, 0, ["RCON not available"]
    
    executed_count = 0
    skipped_count = 0
    errors = []
    
    try:
        mcr = MCRcon(config.RCON_HOST, config.RCON_PASSWORD, port=config.RCON_PORT)
        mcr.connect()
        print("Connected to RCON server")
        
        batch = []
        for username, last_login, days_inactive in inactive_players:
            if check_chunks:
                has_chunks, chunk_count, chunk_list = check_player_has_chunks(username)
                if not has_chunks and chunk_count == 0:
                    print(f"Skipping {username}: No chunks claimed")
                    skipped_count += 1
                    continue
                elif chunk_count == -1:
                    print(f"Warning: Could not verify chunks for {username}, executing command anyway")
                elif chunk_count > 0:
                    print(f"Player {username} has {chunk_count} claimed chunks, executing unclaim command")
            
            command = f"admin unclaim_all {username}"
            batch.append((username, command))
            
            if len(batch) >= batch_size:
                # Execute batch
                for player, cmd in batch:
                    try:
                        response = mcr.command(cmd)
                        print(f"Executed: /{cmd} -> {response}")
                        executed_count += 1
                    except Exception as e:
                        error_msg = f"Failed to execute command for {player}: {e}"
                        print(error_msg)
                        errors.append(error_msg)
                
                batch = []
                if delay_between_batches > 0:
                    print(f"Waiting {delay_between_batches} seconds before next batch...")
                    time.sleep(delay_between_batches)
        
        # Execute remaining commands in the last batch
        if batch:
            for player, cmd in batch:
                try:
                    response = mcr.command(cmd)
                    print(f"Executed: /{cmd} -> {response}")
                    executed_count += 1
                except Exception as e:
                    error_msg = f"Failed to execute command for {player}: {e}"
                    print(error_msg)
                    errors.append(error_msg)
        
        mcr.disconnect()
        print("Disconnected from RCON server")
        
    except Exception as e:
        error_msg = f"RCON connection error: {e}"
        print(error_msg)
        errors.append(error_msg)
        return executed_count, skipped_count, errors
    
    return executed_count, skipped_count, errors

def main():
    parser = argparse.ArgumentParser(description='Find inactive players and generate/execute unclaim commands')
    parser.add_argument('--days', type=int, default=180, 
                       help='Number of days of inactivity (default: 180)')
    parser.add_argument('--output', type=str, 
                       help='Output file for commands (default: print to console)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without generating commands')
    parser.add_argument('--show-details', action='store_true',
                       help='Show detailed information about inactive players')
    parser.add_argument('--execute-rcon', action='store_true',
                       help='Execute commands directly via RCON instead of just generating them')
    parser.add_argument('--batch-size', type=int, default=5,
                       help='Number of commands to send per RCON batch (default: 5)')
    parser.add_argument('--batch-delay', type=float, default=2.0,
                       help='Delay in seconds between RCON batches (default: 2.0)')
    parser.add_argument('--skip-chunk-check', action='store_true',
                       help='Skip checking if players have claimed chunks (faster but less precise)')
    
    # If chunk checking is not available, force skip-chunk-check
    if not CHUNK_CHECK_AVAILABLE:
        print("Note: Chunk checking not available - will skip chunk verification")
    
    args = parser.parse_args()
    
    # Force skip chunk check if not available
    if not CHUNK_CHECK_AVAILABLE:
        args.skip_chunk_check = True
    
    print(f"Searching for players inactive for more than {args.days} days...")
    print("Excluding known staff: MatzE_, KingBBQ42, <KingBBQ42>, Layre")
    
    # Get inactive players
    inactive_players = get_inactive_players(args.days)
    
    if not inactive_players:
        print("No inactive players found!")
        return
    
    print(f"\nFound {len(inactive_players)} inactive players:")
    
    if args.show_details:
        print("\nDetailed player information:")
        print("-" * 80)
        print(f"{'Username':<20} {'Last Login':<20} {'Days Inactive':<15} {'Chunks':<10}")
        print("-" * 80)
        
        for username, last_login, days_inactive in inactive_players:
            last_login_str = last_login if last_login else "Never"
            
            # Show chunk information if requested
            chunk_info = "Unknown"
            if not args.skip_chunk_check:
                try:
                    has_chunks, chunk_count, _ = check_player_has_chunks(username)
                    if chunk_count == -1:
                        chunk_info = "Error"
                    elif chunk_count == 0:
                        chunk_info = "None"
                    else:
                        chunk_info = str(chunk_count)
                except:
                    chunk_info = "Error"
            
            print(f"{username:<20} {last_login_str:<20} {str(days_inactive):<15} {chunk_info:<10}")
    else:
        for username, _, _ in inactive_players:
            print(f"  - {username}")
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would process {len(inactive_players)} players")
        if not args.skip_chunk_check:
            print("Note: Would check for claimed chunks before executing commands")
        print("Use --show-details to see player information")
        print("Remove --dry-run to generate/execute actual commands")
    elif args.execute_rcon:
        if not RCON_AVAILABLE:
            print("\nError: RCON execution requested but RCON is not available!")
            print("Make sure 'mcrcon' is installed and config.py exists with RCON settings")
            return
        
        print(f"\nExecuting unclaim commands via RCON for {len(inactive_players)} players...")
        print(f"Batch size: {args.batch_size}, Delay between batches: {args.batch_delay}s")
        
        if not args.skip_chunk_check:
            print("Checking for claimed chunks before executing commands...")
        
        confirmation = input("Are you sure you want to execute these commands? (y/N): ")
        if confirmation.lower() != 'y':
            print("Cancelled.")
            return
        
        executed, skipped, errors = execute_unclaim_commands_via_rcon(
            inactive_players, 
            batch_size=args.batch_size,
            delay_between_batches=args.batch_delay,
            check_chunks=not args.skip_chunk_check
        )
        
        print(f"\nSummary:")
        print(f"  Commands executed: {executed}")
        print(f"  Players skipped: {skipped}")
        print(f"  Errors: {len(errors)}")
        
        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")
        
    else:
        print(f"\nGenerating unclaim commands for {len(inactive_players)} players...")
        commands = generate_unclaim_commands(
            inactive_players, 
            args.output, 
            check_chunks=not args.skip_chunk_check
        )
        
        if not args.output:
            print(f"\nGenerated {len(commands)} commands (printed above)")
            print("Use --output <filename> to save commands to a file")
            print("Use --execute-rcon to execute commands directly via RCON")

if __name__ == "__main__":
    main()
