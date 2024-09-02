import re
import time
from mcrcon import MCRcon
import config
import database 
import nbt_reader
def send_rcon_command(commands):
    mcr = MCRcon(config.RCON_HOST, config.RCON_PASSWORD, port=config.RCON_PORT)
    mcr.connect()
    for command in commands:
        response = mcr.command(command)
        print(response)
    mcr.disconnect()

def welcome_user(username):
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

def respond_to_message(username, message):
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

def read_new_lines(log_file, last_position):
    with open(log_file, 'r') as file:
        file.seek(last_position)
        lines = file.readlines()
        last_position = file.tell()
    return lines, last_position

def parse_logs(lines):
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

if __name__ == "__main__":
    database.initialize_database()
    last_position = 0
    while True:
        lines, last_position = read_new_lines(config.LOG_FILE, last_position)
        parse_logs(lines)
        time.sleep(3)

