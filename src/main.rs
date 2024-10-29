mod player_status {
    pub mod fetch;
    pub mod monitor;
    pub mod status;
  }
  
  use player_status::status::initialize_status_file;
  use player_status::monitor::monitor_log_file;
  use player_status::fetch::fetch_song_info;
  
  #[tokio::main]
  async fn main() {
    // Initialize the status file
    initialize_status_file();
  
      // Start monitoring the log file
      if let Err(e) = monitor_log_file().await {
        println!("Error monitoring log file: {:?}", e);
    }
  
    // Fetch song info
    if let Err(e) = fetch_song_info("some_song_id").await {
        println!("Error fetching song info: {:?}", e);
    }
  }