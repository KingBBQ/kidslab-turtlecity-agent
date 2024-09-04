import re
import time
from mcrcon import MCRcon
import config
import database 
import nbt_reader
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_rcon_command(commands):
    try:
        mcr = MCRcon(config.RCON_HOST, config.RCON_PASSWORD, port=config.RCON_PORT)
        mcr.connect()
        for command in commands:
            response = mcr.command(command)
            logging.info(f"RCON Response: {response}")
        mcr.disconnect()
    except Exception as e:
        logging.error(f"Error sending RCON command: {e}")

def welcome_user(username):
    try:
        commands = []
        commands.append(f"say Herzlich Willkommen {username} auf TurtleCity!")
        last_seen_datetime, days_since_last_seen, claimed_chunks = nbt_reader.getPlayerStats(username)
        if last_seen_datetime is None:
            commands.append("say Dies ist dein erster Besuch!")
        else:
            commands.append(f"say Du warst zuletzt am {last_seen_datetime.strftime('%d.%m.%Y')} online.")
            commands.append(f"say Das ist {days_since_last_seen} Tage her.")
        if claimed_chunks:
            commands.append(f"say Du hast {len(claimed_chunks)} Chunks geclaimed.")
        if commands:
            send_rcon_command(commands)
        database.update_last_login(username)
    except Exception as e:
        logging.error(f"Error in welcome_user: {e}")

def respond_to_message(username, message):
    try:
        commands = []
        if "hello" in message.lower():
            commands.append(f"say Hello {username}!")
        elif message.strip() == "!zeit":
            players = database.get_recent_players()
            if players:
                commands.append("say Players logged in the last 180 days:")
                for player in players:
                    response = f"{player[0]} - Last Login: {player[1]}, Logins: {player[2]}, Total Time: {player[3]} minutes"
                    commands.append(f"say {response}")
            else:
                commands.append("say No players have logged in the last 180 days.")
        if commands:
            send_rcon_command(commands)
    except Exception as e:
        logging.error(f"Error in respond_to_message: {e}")

def read_new_lines(log_file, last_position):
    try:
        with open(log_file, 'r') as file:
            file.seek(last_position)
            lines = file.readlines()
            last_position = file.tell()
        return lines, last_position
    except Exception as e:
        logging.error(f"Error reading new lines from log file: {e}")
        return [], last_position

def parse_logs(lines):
    try:
        for line in lines:
            print(f"Chat: {line}")
            if "joined the game" in line:
                match = re.search(r'\[.*\]: (.*) joined the game', line)
                if match:
                    username = match.group(1)
                    welcome_user(username)
            elif "left the game" in line:
                match = re.search(r'\[.*\]: (.*) left the game', line)
                if match:
                    username = match.group(1)
                    database.update_last_logout(username)
                    database.update_total_time(username)
            elif "]: <" in line:
                print("Chat message")
                match = re.search(r'\[.*\]: <(.*)> (.*)', line)
                if match:
                    username, message = match.groups()
                    respond_to_message(username, message)
    except Exception as e:
        logging.error(f"Error parsing logs: {e}")

if __name__ == "__main__":
    try:
        database.initialize_database()
        last_position = 0
        while True:
            lines, last_position = read_new_lines(config.LOG_FILE, last_position)
            parse_logs(lines)
            time.sleep(3)
    except Exception as e:
        logging.error(f"Error in main loop: {e}")

