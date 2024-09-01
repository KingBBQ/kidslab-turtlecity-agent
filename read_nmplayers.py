from nbt import nbt
import io
from datetime import datetime
import json

# Path to the NBT file
nbt_file_path = 'latmod/LMPlayers.dat'
# Path to the JSON file
json_file_path = 'latmod/ClaimedChunks.json'

def load_nbt_file(file_path):
    with open(file_path, 'rb') as file:
        data_buffer = file.read()
    buffer = io.BytesIO(data_buffer)
    return nbt.NBTFile(buffer=buffer)

def get_player_by_name(nbt_data, player_name):
    for i in range(len(nbt_data["Players"])):
        if nbt_data["Players"][i]["Name"].value == player_name:
            return nbt_data["Players"][i]
    return None

def get_claimed_chunks_by_uuid(json_file_path, player_uuid):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    claimed_chunks = []
    for level in data.values():
        if player_uuid in level:
            claimed_chunks.extend(level[player_uuid])
    return claimed_chunks

data = load_nbt_file(nbt_file_path)

player = get_player_by_name(data, "Ananrael")

if player:
    last_seen_timestamp = player['Stats']['LastSeen'].value
    # Convert milliseconds to seconds
    last_seen_datetime = datetime.fromtimestamp(last_seen_timestamp / 1000)
    current_datetime = datetime.now()
    days_since_last_seen = (current_datetime - last_seen_datetime).days

    print(f"Last seen: {last_seen_datetime}")
    print(f"Days since last seen: {days_since_last_seen}")

    player_uuid = player['UUID'].value
    claimed_chunks = get_claimed_chunks_by_uuid(json_file_path, player_uuid)
    if claimed_chunks:
        print(f"Claimed Chunks for UUID {player_uuid}: {claimed_chunks}")
    else: 
        print("No claimed chunks found")
else:
    print("Player not found")

    


