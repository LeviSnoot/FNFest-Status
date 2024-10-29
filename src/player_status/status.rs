use std::fs;
use std::path::Path;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct Status {
    pub current_song: Option<String>,
    pub current_artist: Option<String>,
    pub current_instrument: Option<String>,
    pub current_intensity: Option<String>,
    pub current_difficulty: Option<String>,
    pub current_album_art: Option<String>,
    pub icon_bass: Option<String>,
    pub icon_lead: Option<String>,
    pub icon_vocals: Option<String>,
    pub song_state: bool,
    pub is_game_running: bool,
    pub game_mode: Option<String>,
    pub is_backstage: bool,
    pub round_number: u32,
    pub in_song_results: bool,
    pub duration: Option<u32>,
    pub playback_start_time: Option<u64>,
}

pub fn initialize_status_file() {
    let status_file_path = Path::new("status.json");

    if !status_file_path.exists() {
        let initial_status = Status {
            current_song: None,
            current_artist: None,
            current_instrument: None,
            current_intensity: None,
            current_difficulty: None,
            current_album_art: None,
            icon_bass: None,
            icon_lead: None,
            icon_vocals: None,
            song_state: false,
            is_game_running: false,
            game_mode: None,
            is_backstage: false,
            round_number: 1,
            in_song_results: false,
            duration: None,
            playback_start_time: None,
        };
        write_status_to_file(status_file_path.to_str().expect("Invalid path"), &initial_status);
    }
}

pub fn read_status_from_file(path: &str) -> Status {
    let data = fs::read_to_string(path).expect("Unable to read file");
    serde_json::from_str(&data).expect("Unable to parse JSON")
}

pub fn write_status_to_file(path: &str, status: &Status) {
    let data = serde_json::to_string_pretty(status).expect("Unable to serialize JSON");
    fs::write(path, data).expect("Unable to write file");
}