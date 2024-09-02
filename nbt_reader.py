from nbt import nbt
import io
from datetime import datetime
import json
import config

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

data = load_nbt_file(config.NBT_FILE)


def getPlayerStats(playername):
    player = get_player_by_name(data, playername)
    if player:
        last_seen_timestamp = player['Stats']['LastSeen'].value
        last_seen_datetime = datetime.fromtimestamp(last_seen_timestamp / 1000)
        current_datetime = datetime.now()
        days_since_last_seen = (current_datetime - last_seen_datetime).days

        player_uuid = player['UUID'].value
        claimed_chunks = get_claimed_chunks_by_uuid(config.CLAIMED_JSON, player_uuid)
        return last_seen_datetime, days_since_last_seen, claimed_chunks
    else:
        return None, None, None


