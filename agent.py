import re
import time
from mcrcon import MCRcon
from config import RCON_HOST, RCON_PORT, RCON_PASSWORD, LOG_FILE
from database import initialize_database, update_last_login, update_last_logout, update_total_time

def send_rcon_command(command):
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        response = mcr.command(command)
        print(response)

def welcome_user(username):
    command = f"say Welcome {username} to the server!"
    send_rcon_command(command)
    update_last_login(username)

def respond_to_message(username, message):
    if "hello" in message.lower():
        command = f"say Hello {username}!"
        send_rcon_command(command)

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
                update_last_logout(username)
                update_total_time(username)
        elif "]: <" in line:
            print("Chat message")
            match = re.search(r'\[.*\]: <(.*)> (.*)', line)
            if match:
                username, message = match.groups()
                respond_to_message(username, message)

if __name__ == "__main__":
    initialize_database()
    last_position = 0
    while True:
        lines, last_position = read_new_lines(LOG_FILE, last_position)
        parse_logs(lines)
        time.sleep(10)

