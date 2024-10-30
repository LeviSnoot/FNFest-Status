use reqwest::Error;
use serde_json::Value;

pub const ALBUM_ART_URL_PREFIX: &str =
    "https://levisnoot.github.io/fnfest-artwork-store/album_art/";

pub async fn fetch_song_info(song_id: &str) -> Result<Value, Error> {
    let url =
        format!("https://levisnoot.github.io/FNFest-Content-API/api/track_api/{}.json", song_id);
    let response = reqwest::get(&url).await?;
    let song_info: Value = response.json().await?;
    Ok(song_info)
}
