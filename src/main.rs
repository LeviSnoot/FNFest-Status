use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::{env, path::PathBuf};
use sysinfo::System;
use tokio::sync::Mutex;
use notify::{RecommendedWatcher, RecursiveMode, Watcher};
use std::io::{BufRead, BufReader};
use std::fs::File;


#[derive(Serialize, Deserialize, Debug)]
struct Status {
    current_song: Option<String>,
    current_artist: Option<String>,
    current_instrument: Option<String>,
    current_intensity: Option<String>,
    current_difficulty: Option<String>,
    current_album_art: Option<String>,
    icon_bass: Option<String>,
    icon_guitar: Option<String>,
    icon_vocals: Option<String>,
    song_state: bool,
    is_game_running: bool,
    is_battle_stage: bool,
    in_backstage: bool,
    round_number: i32,
    in_song_results: bool,
    duration: Option<f64>,
    playback_start_time: Option<f64>,
}

impl Default for Status {
    fn default() -> Self {
        Status {
            current_song: None,
            current_artist: None,
            current_instrument: None,
            current_intensity: None,
            current_difficulty: None,
            current_album_art: None,
            icon_bass: None,
            icon_guitar: None,
            icon_vocals: None,
            song_state: false,
            is_game_running: false,
            is_battle_stage: false,
            in_backstage: false,
            round_number: 1,
            in_song_results: false,
            duration: None,
            playback_start_time: None,
        }
    }
}

struct GameState {
    status: Arc<Mutex<Status>>,
    system: Arc<Mutex<System>>,
    last_message: Arc<Mutex<String>>,
}

impl GameState {
    fn new() -> Self {
        Self {
            status: Arc::new(Mutex::new(Status::default())),
            system: Arc::new(Mutex::new(System::new())),
            last_message: Arc::new(Mutex::new(String::new())),
        }
    }

    async fn print_status(&self, message: &str) {
        let mut last_msg = self.last_message.lock().await;
        if *last_msg != message {
            println!("{}", message);
            *last_msg = message.to_string();
        }
    }

    async fn is_game_running(&self) -> bool {
        let mut system = self.system.lock().await;
        system.refresh_processes(
            sysinfo::ProcessesToUpdate::All,
            true
        );
        let is_running = system
            .processes()
            .values()
            .any(|process| process.name() == "FortniteClient-Win64-Shipping.exe");
    
        if is_running {
            self.print_status("Fortnite is running").await;
        } else {
            self.print_status("Waiting for Fortnite to start...").await;
        }
        is_running
    }

    async fn update_game_running_state(&self) {
        let mut status = self.status.lock().await;
        status.is_game_running = self.is_game_running().await;
    }

    fn get_log_file_path() -> PathBuf {
        let local_app_data = env::var("LOCALAPPDATA").expect("LOCALAPPDATA environment variable not found");
        PathBuf::from(local_app_data)
            .join("FortniteGame")
            .join("Saved")
            .join("Logs")
            .join("FortniteGame.log")
    }

    async fn parse_log_line(&self, line: &str) {
        // Song playback detection
        if line.contains("LogPilgrimMusicBattle: Client -1 received song to play:") {
            let song_id = line.split("received song to play: ")
                .nth(1)
                .and_then(|s| s.split(" - ").next())
                .map(|s| s.trim().to_lowercase());
            
            if let Some(song_id) = song_id {
                self.print_status(&format!("Song gameplay started: {}", song_id)).await;
                // We'll implement song info fetching next
            }
        }
    
        // Backstage detection
        if line.contains("LogPilgrimQuickplayStateMachine: Display: (Client -1)Entering Pilgrim Quickplay state EPilgrimQuickplayState::Pregame") {
            let mut status = self.status.lock().await;
            status.in_backstage = true;
            self.print_status("Entered backstage area").await;
        }
    
        if line.contains("LogPilgrimQuickplayStateMachine: Display: (Client -1)Leaving Pilgrim Quickplay state EPilgrimQuickplayState::Pregame") {
            let mut status = self.status.lock().await;
            status.in_backstage = false;
            self.print_status("Left backstage area").await;
        }
    }

    async fn monitor_log_file(&self) -> Result<()> {
        let log_path = Self::get_log_file_path();
        self.print_status(&format!("Monitoring log file at: {}", log_path.display())).await;
    
        let (tx, mut rx) = tokio::sync::mpsc::channel(100);
    
        let mut watcher = RecommendedWatcher::new(
            move |res| {
                tx.blocking_send(res).unwrap();
            },
            notify::Config::default(),
        )?;

        watcher.watch(&log_path, RecursiveMode::NonRecursive)?;

        let file = File::open(&log_path)?;
        let mut reader = BufReader::new(file);
        let mut line = String::new();

        while let Some(res) = rx.recv().await {
            match res {
                Ok(_) => {
                    while reader.read_line(&mut line)? > 0 {
                        self.parse_log_line(&line).await;
                        line.clear();
                    }
                }
                Err(e) => self.print_status(&format!("Watch error: {:?}", e)).await,
            }
        }
        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let game_state = Arc::new(GameState::new());
    
    let monitor_state = game_state.clone();
    let log_monitor_state = game_state.clone();
    
    tokio::spawn(async move {
        loop {
            monitor_state.update_game_running_state().await;
            tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
        }
    });

    tokio::spawn(async move {
        if let Err(e) = log_monitor_state.monitor_log_file().await {
            println!("Error monitoring log file: {:?}", e);
        }
    });

    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}