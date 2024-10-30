use crate::player_status::fetch::{ fetch_song_info, ALBUM_ART_URL_PREFIX };
use crate::player_status::status::{ read_status_from_file, write_status_to_file };
use notify::{ Config, EventKind, RecommendedWatcher, RecursiveMode, Result, Watcher };
use std::collections::HashMap;
use std::env;
use std::fs::OpenOptions;
use std::io::{ BufRead, BufReader, Seek, SeekFrom };
use std::path::PathBuf;
use std::sync::mpsc::channel;

pub fn get_log_file_path() -> PathBuf {
    let local_app_data = env
        ::var("LOCALAPPDATA")
        .expect("LOCALAPPDATA environment variable not set");
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

    // Seek to the end of the file initially to only read new lines
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

    if
        line.contains(
            "LogAthenaMatchmakingWidget: UFortAthenaMatchmakingWidgetLegacy::RequestMatchmakingStart"
        )
    {
        println!("Matchmaking started.");
        status.is_game_running = true;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogMatchmakingServiceClient: HandleError - Type: 'Canceled'") {
        println!("Matchmaking canceled.");
        status.is_game_running = false;
        write_status_to_file("status.json", &status);
    } else if
        line.contains(
            "LogFortPlaytimeManager: UFortPlaytimeManager::SetPlaytimeState - Changing Playtime State from Unblocked to Sleep"
        )
    {
        println!("Player entered Sleep Mode.");
        status.is_game_running = false;
        write_status_to_file("status.json", &status);
    } else if
        line.contains(
            "LogFortPlaytimeManager: UFortPlaytimeManager::SetPlaytimeState - Changing Playtime State from Sleep to Unblocked"
        )
    {
        println!("Player left Sleep Mode.");
        status.is_game_running = true;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimMusicBattle: Client -1 received song to play:") {
        println!("Song gameplay started.");
        if let Some(song_id) = extract_song_id(line) {
            status.song_id = Some(song_id.clone()); // Store song_id in status
            match fetch_song_info(&song_id).await {
                Ok(song_info) => {
                    if let Some(track) = song_info.get("track") {
                        status.current_song = track
                            .get("trackTitle")
                            .and_then(|v| v.as_str())
                            .map(String::from);
                        status.current_artist = track
                            .get("artistName")
                            .and_then(|v| v.as_str())
                            .map(String::from);
                        status.icon_bass = track
                            .get("iconBass")
                            .and_then(|v| v.as_str())
                            .map(String::from);
                        status.icon_lead = track
                            .get("iconGuitar")
                            .and_then(|v| v.as_str())
                            .map(String::from);
                        status.icon_vocals = track
                            .get("iconVocals")
                            .and_then(|v| v.as_str())
                            .map(String::from);
                        status.duration = track
                            .get("duration")
                            .and_then(|v| v.as_u64())
                            .map(|v| v as u32);

                        if
                            let Some(album_art_filename) = track
                                .get("albumArtFilename")
                                .and_then(|v| v.as_str())
                        {
                            status.current_album_art = Some(
                                format!("{}{}", ALBUM_ART_URL_PREFIX, album_art_filename)
                            );
                        }

                        write_status_to_file("status.json", &status);
                    }
                }
                Err(e) => println!("Error fetching song info: {:?}", e),
            }
        }
    } else if line.contains("Playback reached end at play position") {
        println!("Song finished playing.");
        status.current_song = None;
        status.current_intensity = None;
        write_status_to_file("status.json", &status);
    } else if
        line.contains(
            "LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::Pregame"
        )
    {
        println!("Entering Pregame state (backstage).");
        status.is_backstage = true;
        write_status_to_file("status.json", &status);
    } else if
        line.contains(
            "LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::Pregame"
        )
    {
        println!("Leaving Pregame state (no longer backstage).");
        status.is_backstage = false;
        write_status_to_file("status.json", &status);
    } else if
        line.contains(
            "LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::SongResults"
        )
    {
        println!("Entering Song Results state.");
        status.in_song_results = true;
        write_status_to_file("status.json", &status);
    } else if
        line.contains(
            "LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::SongResults"
        )
    {
        println!("Leaving Song Results state.");
        status.in_song_results = false;
        write_status_to_file("status.json", &status);
    } else if line.contains("LogPilgrimGemBreakListener: UPilgrimGemBreakListener::Init:") {
        println!("Processing instrument and difficulty...");
        if let Some((instrument, difficulty)) = extract_instrument_and_difficulty(line) {
            println!("Instrument: {}, Difficulty: {}", instrument, difficulty);
            status.current_instrument = Some(instrument.clone());
            status.current_difficulty = Some(difficulty);

            // Fetch song_info using song_id from status
            if let Some(song_id) = &status.song_id {
                match fetch_song_info(song_id).await {
                    Ok(song_info) => {
                        if let Some(track) = song_info.get("track") {
                            // Map instrument to instrument_key
                            let intensity_mapping = HashMap::from([
                                ("bass", "bass"),
                                ("drum", "drums"),
                                ("lead", "guitar"),
                                ("vocals", "vocals"),
                                ("pro lead", "proGuitar"),
                                ("pro bass", "proBass"),
                            ]);
                            let instrument_lower = instrument.to_lowercase();
                            let instrument_str = instrument.as_str();
                            let instrument_key = intensity_mapping
                                .get(instrument_lower.as_str())
                                .unwrap_or(&instrument_str);

                            if
                                let Some(intensities) = track
                                    .get("intensities")
                                    .and_then(|v| v.as_object())
                            {
                                if
                                    let Some(intensity_value) = intensities
                                        .get(*instrument_key)
                                        .and_then(|v| v.as_f64())
                                {
                                    status.current_intensity = Some(intensity_value);
                                    println!("Intensity for {}: {}", instrument, intensity_value);
                                } else {
                                    println!("Instrument key '{}' not found in intensities.", instrument_key);
                                }
                            }
                            // Update status
                            write_status_to_file("status.json", &status);
                        }
                    }
                    Err(e) => println!("Error fetching song info: {:?}", e),
                }
            } else {
                println!("No song_id available to fetch song info.");
            }
        }
    }
}

fn extract_song_id(line: &str) -> Option<String> {
    let song_id_mapping: HashMap<&str, &str> = [
        ("astronautintheocean", "astronoutintheocean"),
        ("theedgeofglory", "edgeofglory"),
    ]
        .iter()
        .cloned()
        .collect();

    let song_id = line.split("received song to play: ").nth(1)?.split(" - ").next()?;

    Some(song_id_mapping.get(song_id).unwrap_or(&song_id).to_string())
}

fn extract_instrument_and_difficulty(line: &str) -> Option<(String, String)> {
    let parts: Vec<&str> = line.split("using track ").nth(1)?.split(" and Difficulty ").collect();
    if parts.len() == 2 {
        let raw_instrument = parts[0].split("::").last()?.replace("Track", "").to_lowercase();
        let difficulty = parts[1].split("::").last()?.replace("Difficulty", "").trim().to_string();

        let instrument = format_instrument_name(&raw_instrument);

        Some((instrument, difficulty))
    } else {
        None
    }
}

fn format_instrument_name(instrument: &str) -> String {
    let instrument_mapping = HashMap::from([
        ("bass", "Bass"),
        ("drum", "Drums"),
        ("guitar", "Lead"),
        ("vocals", "Vocals"),
        ("plasticguitar", "Pro Lead"),
        ("plasticbass", "Pro Bass"),
    ]);

    let instrument = instrument.trim().to_lowercase();

    instrument_mapping
        .get(instrument.as_str())
        .map(|s| s.to_string())
        .unwrap_or_else(|| instrument.to_string())
}
