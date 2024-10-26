import json
import os
import time
import sys
import configparser
from pypresence import Presence, ActivityType

# Path to the config file
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')

# Path to the status file
STATUS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'status.json')

# Read the client ID from the config file
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_FILE_PATH):
    print("Error: config.ini file not found.", flush=True)
    sys.exit(1)

config.read(CONFIG_FILE_PATH)
CLIENT_ID = config.get('DISCORD', 'client_id', fallback=None)

if not CLIENT_ID:
    print("Error: client_id not set in config.ini.", flush=True)
    sys.exit(1)

# Initialize the Discord RPC client
rpc = Presence(CLIENT_ID)
rpc.connect()

# Track the last presence state and last update time to reduce console spam and avoid rate limiting
last_presence = None
last_update_time = 0
UPDATE_INTERVAL = 1  # Check for changes every second
MIN_UPDATE_INTERVAL = 15  # Minimum interval between updates to avoid rate limiting
GRACE_PERIOD = 20  # Grace period to wait before clearing presence
last_printed_message = None  # Track the last printed message

def read_status_from_file():
    with open(STATUS_FILE_PATH, 'r') as f:
        return json.load(f)

def get_small_image_url(status_data):
    base_url = 'https://levisnoot.github.io/fnfest-artwork-store/instrument_icons/'
    current_instrument = status_data['current_instrument'].lower()

    # Map current_instrument to its corresponding icon key
    instrument_icon_mapping = {
        'lead': 'icon_guitar',
        'bass': 'icon_bass',
        'vocals': 'icon_vocals',
        'pro lead': 'icon_guitar',
        'pro bass': 'icon_bass'
    }

    icon_key = instrument_icon_mapping.get(current_instrument, '')
    icon_value = status_data.get(icon_key, '')

    if icon_value == 'Keyboard':
        if current_instrument == 'pro lead' or current_instrument == 'pro bass':
            return base_url + 'pro_synth_bg.png'
        else:
            return base_url + 'synth_bg.png'
    
    instrument_mapping = {
        'bass': 'bass_bg.png',
        'drums': 'drums_bg.png',
        'lead': 'lead_bg.png',
        'vocals': 'vocals_bg.png',
        'pro lead': 'pro_lead_bg.png',
        'pro bass': 'pro_bass_bg.png'
    }
    return base_url + instrument_mapping.get(current_instrument, 'default.png')

def print_message(message):
    global last_printed_message
    if message != last_printed_message:
        print(message, flush=True)
        last_printed_message = message

def format_presence_message(presence):
    details = presence.get('details', 'N/A')
    state = presence.get('state', 'N/A')
    large_text = presence.get('large_text', 'N/A')
    return f"Updated Presence -> Details: {details} | State: {state} | Text: {large_text}"

def update_presence():
    global last_presence, last_update_time, last_printed_message
    status_data = read_status_from_file()

    presence = None

    if status_data['in_backstage']:
        if status_data.get('is_battle_stage', False):
            activity_type = ActivityType.COMPETING
            details = "Battle Stage"
            state = "Backstage | Waiting for game to start..."
        else:
            activity_type = ActivityType.PLAYING
            details = "Main Stage"
            state = "Backstage | Selecting song(s)..."
        presence = {
            'activity_type': activity_type,
            'details': details,
            'state': state
        }
    elif status_data['in_song_results']:
        if status_data.get('is_battle_stage', False):
            activity_type = ActivityType.COMPETING
            details = "Battle Stage"
            round_number = status_data.get('round_number', 1)
            if round_number >= 5:
                state = "Intermission | Receiving final score..."
            else:
                state = "Intermission | Waiting for next round..."
        else:
            activity_type = ActivityType.PLAYING
            details = "Main Stage"
            state = "Intermission | Receiving score..."
        presence = {
            'activity_type': activity_type,
            'details': details,
            'state': state
        }
    elif status_data['song_state']:
        playback_start_time = status_data.get('playback_start_time')
        duration = status_data.get('duration')

        # Ensure playback_start_time and duration are not None
        if playback_start_time is None or duration is None:
            print_message("Waiting for valid playback start time and duration...")
            return

        small_image_url = get_small_image_url(status_data)

        game_mode = "Battle Stage" if status_data.get('is_battle_stage', False) else "Main Stage"

        # Determine the round information
        if status_data.get('is_battle_stage', False):
            round_number = status_data.get('round_number', 1)
            if round_number == 4:
                round_info = "Final Round"
            else:
                round_info = f"Round {round_number}"
            state = f"{game_mode} | {round_info}"
        else:
            state = game_mode

        presence = {
            'activity_type': ActivityType.LISTENING,
            'details': f"{status_data['current_song']} - {status_data['current_artist']}",
            'state': state,
            'large_image': status_data['current_album_art'],
            'large_text': f"{status_data['current_instrument']} | {status_data['current_difficulty']}",
            'small_image': small_image_url,
            'small_text': f"{status_data['current_instrument']} | {status_data['current_difficulty']}",
            'start': int(playback_start_time),
            'end': int(playback_start_time + duration)
        }

    current_time = time.time()
    if presence != last_presence and (current_time - last_update_time >= MIN_UPDATE_INTERVAL):
        if presence:
            rpc.update(**presence)
            print_message(format_presence_message(presence))
        last_presence = presence
        last_update_time = current_time
    elif presence is None and last_presence is not None:
        # Start grace period timer
        if current_time - last_update_time >= GRACE_PERIOD:
            rpc.clear()
            print_message('Presence cleared')
            last_presence = None

    # Clear presence if all relevant status flags are False and grace period has passed
    if not status_data['song_state'] and not status_data['in_backstage'] and not status_data['in_song_results']:
        if last_presence is not None and current_time - last_update_time >= GRACE_PERIOD:
            rpc.clear()
            print_message('Presence cleared')
            last_presence = None

if __name__ == "__main__":
    try:
        while True:
            update_presence()
            time.sleep(UPDATE_INTERVAL)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        rpc.clear()
        rpc.close()