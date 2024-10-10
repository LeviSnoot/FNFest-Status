# Created by LeviSnoot
# https://github.com/LeviSnoot/FNFest-Status

import os
import time
import psutil
import json
import requests
from datetime import datetime, timedelta
import sys

# Path to the status file
status_file_path = os.path.join(os.path.dirname(__file__), 'status.json')

# Initial status values
initial_status = {
    "current_song": None,
    "current_artist": None,
    "current_instrument": None,
    "current_intensity": None,
    "current_difficulty": None,
    "current_album_art": None,
    "song_state": False,
    "is_game_running": False,
    "is_battle_stage": False,
    "in_backstage": False,
    "in_song_results": False
}

# Check if the status file exists, if not create it with initial values
if not os.path.exists(status_file_path):
    with open(status_file_path, 'w') as f:
        json.dump(initial_status, f)
    print(f"Created initial status file at {status_file_path}")
    sys.stdout.flush()

def write_status_to_file(status):
    with open(status_file_path, 'w') as f:
        json.dump(status, f)

def read_status_from_file():
    with open(status_file_path, 'r') as f:
        return json.load(f)

# Path to the log file
log_file_path = os.path.expandvars(r'%localappdata%\FortniteGame\Saved\Logs\FortniteGame.log')
# Validate and sanitize the log file path
if not os.path.isfile(log_file_path):
    raise ValueError(f"Invalid log file path: {log_file_path}")

# Path to the local JSON file
local_json_path = 'spark-tracks.json'
# URL to fetch the API data from
json_url = 'https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game/spark-tracks'
# Path to the file storing the last update time
last_update_file = 'last_update.txt'

# Mapping of known discrepancies between log song IDs and API song IDs
song_id_mapping = {
    'astronautintheocean': 'astronoutintheocean'
}

# Initial state
in_backstage = False
matchmaking_started = False
playing_song = False
current_song = None
current_instrument = None
current_intensity = None
current_difficulty = None
is_battle_stage = False
in_lobby = False
in_sleep_mode = False
game_running_state = False
in_song_results = False

def reset_state():
    global in_backstage, matchmaking_started, playing_song, current_song, current_instrument, current_intensity, current_difficulty, is_battle_stage, in_lobby, in_sleep_mode, game_running_state, in_song_results
    in_backstage = False
    matchmaking_started = False
    playing_song = False
    current_song = None
    current_instrument = None
    current_intensity = None
    current_difficulty = None
    is_battle_stage = False
    in_lobby = False
    in_sleep_mode = False
    game_running_state = False
    in_song_results = False
    print("State has been reset.")
    sys.stdout.flush()
    
    # Update the status file to reflect the reset state
    status = read_status_from_file()
    status.update({
        "current_song": None,
        "current_artist": None,
        "current_instrument": None,
        "current_intensity": None,
        "current_difficulty": None,
        "current_album_art": None,
        "song_state": False,
        "is_game_running": False,
        "is_battle_stage": False,
        "in_backstage": False,
        "in_song_results": False
    })
    write_status_to_file(status)
    print(f"Updated status: {json.dumps(status, indent=4)}")
    sys.stdout.flush()

def update_state(new_state):
    global in_backstage
    if in_backstage != new_state:
        in_backstage = new_state
        status = read_status_from_file()
        status["in_backstage"] = in_backstage
        write_status_to_file(status)
        print(f"Player is {'now in' if in_backstage else 'no longer in'} the backstage area.")
        sys.stdout.flush()

def update_song_state(song, instrument, intensity, difficulty, artist, album_art):
    global playing_song, current_song, current_instrument, current_intensity, current_difficulty
    playing_song = True
    current_song = song
    current_instrument = instrument
    current_intensity = intensity
    current_difficulty = difficulty
    
    # First write to the status file with the information properties
    status = read_status_from_file()
    status.update({
        "current_song": song,
        "current_artist": artist,
        "current_instrument": instrument,
        "current_intensity": intensity,
        "current_difficulty": difficulty,
        "current_album_art": album_art,
        "song_state": False
    })
    write_status_to_file(status)
    print(f"Updated status: {json.dumps(status, indent=4)}")
    sys.stdout.flush()
    print(f"Playing song: {current_song} by {artist}, Instrument: {instrument}, Intensity: {intensity}, Difficulty: {difficulty}")
    sys.stdout.flush()
    print(f"Album Art URL: {album_art}")
    sys.stdout.flush()
    
    # Wait for a few seconds before setting song_state to True
    time.sleep(2)
    
    # Second write to the status file with song_state set to True
    status["song_state"] = True
    write_status_to_file(status)
    print(f"Updated status: {json.dumps({'song_state': True}, indent=4)}")
    sys.stdout.flush()

def end_song_state():
    global playing_song, current_song, current_instrument, current_intensity, current_difficulty, current_artist, current_album_art
    playing_song = False
    
    # First write to the status file with song_state set to False
    status = read_status_from_file()
    status.update({
        "current_song": current_song,
        "current_artist": current_artist,
        "current_instrument": current_instrument,
        "current_intensity": current_intensity,
        "current_difficulty": current_difficulty,
        "current_album_art": current_album_art,
        "song_state": False
    })
    write_status_to_file(status)
    print(f"Updated status: {json.dumps({'song_state': False}, indent=4)}")
    sys.stdout.flush()
    print(f"Finished playing song: {current_song}")
    sys.stdout.flush()
    
    # Wait for a few seconds before resetting the rest of the properties
    time.sleep(2)
    
    # Second write to the status file with all properties reset
    status.update({
        "current_song": None,
        "current_artist": None,
        "current_instrument": None,
        "current_intensity": None,
        "current_difficulty": None,
        "current_album_art": None,
        "song_state": False
    })
    write_status_to_file(status)
    print(f"Updated status: {json.dumps(status, indent=4)}")
    sys.stdout.flush()
    
    # Reset global variables
    current_song = None
    current_instrument = None
    current_intensity = None
    current_difficulty = None
    current_artist = None
    current_album_art = None

def is_game_running():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'FortniteClient-Win64-Shipping.exe':
            return True
    return False

def fetch_json_data():
    if os.path.exists(last_update_file):
        with open(last_update_file, 'r') as f:
            last_updated = datetime.fromisoformat(f.read().strip())
    else:
        last_updated = datetime.min

    if datetime.now() - last_updated > timedelta(hours=3):
        response = requests.get(json_url)
        if response.status_code == 200:
            data = response.json()
            # Update album art URLs
            for track_id, track_data in data.items():
                if isinstance(track_data, dict) and 'track' in track_data:
                    track_info = track_data['track']
                    if isinstance(track_info, dict) and 'au' in track_info:
                        album_art_url = track_info['au']
                        # Extract the filename from the original URL
                        filename = os.path.basename(album_art_url)
                        # Construct the new URL
                        new_album_art_url = f"https://levisnoot.github.io/fnfest-artwork-store/album_art/{filename}"
                        # Update the URL in the data
                        track_info['au'] = new_album_art_url

            with open(local_json_path, 'w') as f:
                json.dump(data, f)
            with open(last_update_file, 'w') as f:
                f.write(datetime.now().isoformat())
            print("API data updated.")
            sys.stdout.flush()
        else:
            print("Failed to fetch API.")
            sys.stdout.flush()
    else:
        print("Using cached API.")
        sys.stdout.flush()

def get_song_info(song_id):
    # Correct the song ID if it exists in the mapping
    corrected_song_id = song_id_mapping.get(song_id, song_id)
    with open(local_json_path, 'r') as f:
        data = json.load(f)
        if corrected_song_id in data:
            return data[corrected_song_id]['track']
        else:
            print(f"Song ID '{corrected_song_id}' not found in API.")
            sys.stdout.flush()
    return None

def format_instrument_name(instrument):
    instrument_mapping = {
        'bass': 'Bass',
        'drum': 'Drums',
        'guitar': 'Lead',
        'vocals': 'Vocals',
        'plasticguitar': 'Pro Lead',
        'plasticbass': 'Pro Bass'
    }
    return instrument_mapping.get(instrument, instrument.capitalize())

def format_difficulty_name(difficulty):
    difficulty_mapping = {
        'DifficultyEasy': 'Easy',
        'DifficultyMedium': 'Medium',
        'DifficultyHard': 'Hard',
        'DifficultyExpert': 'Expert'
    }
    return difficulty_mapping.get(difficulty, difficulty)

def monitor_log_file():
    global matchmaking_started, is_battle_stage, game_running, current_song, current_artist, current_album_art, in_lobby, in_sleep_mode, game_running_state, in_song_results

    game_running = False

    while True:
        if is_game_running():
            if not game_running:
                print("Fortnite has started.")
                sys.stdout.flush()
                game_running = True
                fetch_json_data()
                status = read_status_from_file()
                status["is_game_running"] = True
                write_status_to_file(status)

            with open(log_file_path, 'r') as log_file:
                log_file.seek(0, os.SEEK_END)  # Move to the end of the file

                while is_game_running():
                    line = log_file.readline()
                    if not line:
                        time.sleep(0.1)  # Sleep briefly to avoid busy-waiting
                        continue

                    # Skip checks if in lobby
                    if in_lobby:
                        if 'LogAthenaMatchmakingWidget: UFortAthenaMatchmakingWidgetLegacy::RequestMatchmakingStart' in line:
                            matchmaking_started = True
                            in_lobby = False
                            print("Matchmaking started.")
                            sys.stdout.flush()
                        continue

                    # Check for Matchmaking start
                    if 'LogAthenaMatchmakingWidget: UFortAthenaMatchmakingWidgetLegacy::RequestMatchmakingStart' in line:
                        matchmaking_started = True
                        print("Matchmaking started.")
                        sys.stdout.flush()

                    # Check for Battle Stage mode
                    if 'Playlist_PilgrimBattleStage' in line:
                        is_battle_stage = True
                        status = read_status_from_file()
                        status["is_battle_stage"] = True
                        write_status_to_file(status)
                        print("Battle Stage mode detected.")
                        sys.stdout.flush()

                    # Check for Main Stage mode
                    if 'Playlist_PilgrimQuickplay' in line:
                        is_battle_stage = False
                        status = read_status_from_file()
                        status["is_battle_stage"] = False
                        write_status_to_file(status)
                        print("Main Stage mode detected.")
                        sys.stdout.flush()

                    # Check for entering Pregame state (backstage)
                    if 'LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::Pregame' in line:
                        update_state(True)

                    # Check for leaving Pregame state (no longer backstage)
                    if 'LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::Pregame' in line:
                        update_state(False)

                    # Check for loading into a game
                    if 'LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::Loading' in line:
                        print("Player is loading into a game.")
                        sys.stdout.flush()

                    # Check for Return to Main Menu
                    if 'LogOnlineGame: FortPC::ReturnToMainMenu' in line:
                        if playing_song:
                            end_song_state()  # Ensure the song state is ended
                        reset_state()
                        in_lobby = True
                        print("Player returned to main menu.")
                        sys.stdout.flush()

                    # Check for Song Start
                    if 'LogPilgrimMusicBattle: Client -1 received song to play:' in line:
                        print("Song gameplay started.")
                        sys.stdout.flush()
                        # Extract song ID from the log line and convert to lowercase
                        song_id = line.split('received song to play: ')[1].split(' - ')[0].strip().lower()
                        song_info = get_song_info(song_id)
                        if song_info:
                            current_song = song_info['tt']
                            current_artist = song_info['an']
                            current_album_art = song_info['au']
                        else:
                            current_song = None

                    # Check for Song End
                    if 'LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::SongGameplay' in line:
                        end_song_state()

                    # Check for entering Song Results state (post-game screen)
                    if 'LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::SongResults' in line:
                        in_song_results = True
                        status = read_status_from_file()
                        status["in_song_results"] = True
                        write_status_to_file(status)
                        print("Entering Song Results state.")
                        sys.stdout.flush()

                    # Check for leaving Song Results state (post-game screen)
                    if 'LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::SongResults' in line:
                        in_song_results = False
                        status = read_status_from_file()
                        status["in_song_results"] = False
                        write_status_to_file(status)
                        print("Leaving Song Results state.")
                        sys.stdout.flush()

                    # Check for Instrument and Difficulty
                    if 'LogPilgrimGemBreakListener: UPilgrimGemBreakListener::Init:' in line:
                        parts = line.split('using track ')[1].split(' and Difficulty ')
                        instrument = parts[0].split('::')[-1].replace('Track', '').lower()
                        difficulty = parts[1].split('::')[-1].replace('Difficulty', '').strip()  # Strip whitespace
                        instrument_key = instrument[:2]  # Get the first two letters of the instrument
                        if instrument_key == 'dr':
                            instrument_key = 'ds'  # Correct the instrument key for drums
                        elif instrument_key == 'gu':
                            instrument_key = 'gr'  # Correct the instrument key for lead (guitar)
                        elif instrument_key == 'vo':
                            instrument_key = 'vl'  # Correct the instrument key for vocals
                        elif instrument_key == 'pl':
                            instrument_key = 'pg'  # Correct the instrument key for pro lead (guitar)
                        
                        # Fetch song info if not already fetched
                        if not current_song:
                            song_info = get_song_info(current_song)
                        
                        if song_info and instrument_key in song_info['in']:
                            intensity_value = song_info['in'][instrument_key]
                            formatted_instrument = format_instrument_name(instrument)
                            formatted_difficulty = format_difficulty_name(difficulty)
                            update_song_state(current_song, formatted_instrument, intensity_value, formatted_difficulty, current_artist, current_album_art)
                        else:
                            print(f"Instrument key '{instrument_key}' not found in song info.")
                            sys.stdout.flush()

                    # Check for Matchmaking cancellation
                    if 'LogMatchmakingServiceClient: HandleError - Type: \'Canceled\'' in line:
                        matchmaking_started = False
                        print("Matchmaking canceled.")
                        sys.stdout.flush()

                    # Check for entering Sleep Mode
                    if 'LogFortPlaytimeManager: UFortPlaytimeManager::SetPlaytimeState - Changing Playtime State from Unblocked to Sleep' in line:
                        in_sleep_mode = True
                        print("Player entered Sleep Mode.")
                        sys.stdout.flush()

                    # Check for leaving Sleep Mode
                    if 'LogFortPlaytimeManager: UFortPlaytimeManager::SetPlaytimeState - Changing Playtime State from Sleep to Unblocked' in line:
                        in_sleep_mode = False
                        print("Player left Sleep Mode.")
                        sys.stdout.flush()

            print("Fortnite has stopped.")
            sys.stdout.flush()
            reset_state()
            status = read_status_from_file()
            status["is_game_running"] = False
            write_status_to_file(status)
            game_running = False
        else:
            if game_running:
                print("Fortnite has stopped.")
                sys.stdout.flush()
                reset_state()
                status = read_status_from_file()
                status["is_game_running"] = False
                write_status_to_file(status)
                game_running = False
            print("Waiting for Fortnite to start...")
            sys.stdout.flush()
            time.sleep(5)

if __name__ == "__main__":
    try:
        monitor_log_file()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.stdout.flush()