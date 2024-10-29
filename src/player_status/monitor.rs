use notify::{Config, EventKind, RecommendedWatcher, RecursiveMode, Result, Watcher};
use std::collections::HashMap;
use std::env;
use std::fs::OpenOptions;
use std::io::{BufRead, BufReader, Seek, SeekFrom};
use std::path::PathBuf;
use std::sync::mpsc::channel;
use crate::player_status::status::{read_status_from_file, write_status_to_file};
use crate::player_status::fetch::fetch_song_info;

pub fn get_log_file_path() -> PathBuf {
    let local_app_data =
        env::var("LOCALAPPDATA").expect("LOCALAPPDATA environment variable not set");
    PathBuf::from(local_app_data)
        .join("FortniteGame")
        .join("Saved")
        .join("Logs")
        .join("FortniteGame.log")
}

pub async fn monitor_log_file() -> Result<()> {
    let log_file_path = get_log_file_path();
    let (tx, rx) = channel();

    let mut watcher: RecommendedWatcher = Watcher::new(tx, Config::default())?;
    watcher.watch(&log_file_path, RecursiveMode::NonRecursive)?;

    let file = OpenOptions::new().read(true).open(&log_file_path)?;
    let mut reader = BufReader::new(file);

    reader.seek(SeekFrom::End(0))?;

    loop {
        match rx.recv() {
            Ok(event) => {
                if let EventKind::Modify(_) = event.unwrap().kind {
                    let mut line = String::new();
                    while reader.read_line(&mut line)? > 0 {
                        process_log_line(&line).await;
                        line.clear();
                    }
                }
            }
            Err(e) => println!("watch error: {:?}", e),
        }
    }
}

async fn process_log_line(line: &str) {
    let mut status = read_status_from_file("status.json");

    if line.contains("LogAthenaMatchmakingWidget: UFortAthenaMatchmakingWidgetLegacy::RequestMatchmakingStart") {
        println!("Matchmaking started.");
        status.is_game_running = true;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogMatchmakingServiceClient: HandleError - Type: 'Canceled'") {
        println!("Matchmaking canceled.");
        status.is_game_running = false;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogFortPlaytimeManager: UFortPlaytimeManager::SetPlaytimeState - Changing Playtime State from Unblocked to Sleep") {
        println!("Player entered Sleep Mode.");
        status.is_game_running = false;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogFortPlaytimeManager: UFortPlaytimeManager::SetPlaytimeState - Changing Playtime State from Sleep to Unblocked") {
        println!("Player left Sleep Mode.");
        status.is_game_running = true;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimMusicBattle: Client -1 received song to play:") {
        println!("Song gameplay started.");
        if let Some(song_id) = extract_song_id(line) {
            match fetch_song_info(&song_id).await {
                Ok(song_info) => {
                    if let Some(track) = song_info.get("track") {
                        status.current_song = track.get("trackTitle").and_then(|v| v.as_str()).map(String::from);
                        status.current_artist = track.get("artistName").and_then(|v| v.as_str()).map(String::from);
                        status.icon_bass = track.get("iconBass").and_then(|v| v.as_str()).map(String::from);
                        status.icon_lead = track.get("iconGuitar").and_then(|v| v.as_str()).map(String::from);
                        status.icon_vocals = track.get("iconVocals").and_then(|v| v.as_str()).map(String::from);
                        write_status_to_file("status.json", &status);
                    }
                }
                Err(e) => println!("Error fetching song info: {:?}", e),
            }
    } else if line.contains("Playback reached end at play position") {
        println!("Song finished playing.");
        status.current_song = None;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::Pregame") {
        println!("Entering Pregame state (backstage).");
        status.is_backstage = true;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::Pregame") {
        println!("Leaving Pregame state (no longer backstage).");
        status.is_backstage = false;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::SongResults") {
        println!("Entering Song Results state.");
        status.in_song_results = true;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::SongResults") {
        println!("Leaving Song Results state.");
        status.in_song_results = false;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimGemBreakListener: UPilgrimGemBreakListener::Init:") {
        if let Some((instrument, difficulty)) = extract_instrument_and_difficulty(line) {
            println!("Instrument: {}, Difficulty: {}", instrument, difficulty);
            // Update status with instrument and difficulty
            status.current_instrument = Some(instrument);
            status.current_difficulty = Some(difficulty);
            write_status_to_file("status.json", &status);
        }
    }
}

    // Function to extract and correct the song ID from a log line
    fn extract_song_id(line: &str) -> Option<String> {
        // Define a mapping for known discrepancies between log song IDs and API song IDs
        let song_id_mapping: HashMap<&str, &str> = [
            ("astronautintheocean", "astronoutintheocean"),
            ("theedgeofglory", "edgeofglory"),
        ]
        .iter()
        .cloned()
        .collect();

        // Extract the song ID from the log line
        let song_id = line
            .split("received song to play: ")
            .nth(1)?
            .split(" - ")
            .next()?;

        // Correct the song ID if it exists in the mapping
        Some(song_id_mapping.get(song_id).unwrap_or(&song_id).to_string())
    }

    fn extract_instrument_and_difficulty(line: &str) -> Option<(String, String)> {
        // Logic to extract instrument and difficulty from the log line
        let parts: Vec<&str> = line
            .split("using track ")
            .nth(1)?
            .split(" and Difficulty ")
            .collect();
        if parts.len() == 2 {
            let instrument = parts[0]
                .split("::")
                .last()?
                .replace("Track", "")
                .to_lowercase();
            let difficulty = parts[1]
                .split("::")
                .last()?
                .replace("Difficulty", "")
                .trim()
                .to_string();
            Some((instrument, difficulty))
        } else {
            None
        }
    }
}
