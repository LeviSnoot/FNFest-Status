![](assets/gh-banner.png)

# FNFest-Status
Monitor and display the status of Fortnite Festival events.

## Features
- Displays current song information, difficulty, intensity and album art (the latter through [fnfest-artwork-store](https://github.com/LeviSnoot/fnfest-artwork-store) to avoid excessive fetching on Epic's servers).
- Includes a Flask web app that can be used in OBS to display information on stream.

## What does it do?
The main script (`playerStatus.py`) simply reads your Fortnite log file (located in `%localappdata%\FortniteGame\Saved\Logs\FortniteGame.log`) and filters it for known events relating to Fortnite Festival. It calls on the public [Fortnite Festival Content API](https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game/spark-tracks) to match song ID's from the log to their metadata such as track and artist names.

## Prerequisites
- Python 3.x
- Fortnite
- Windows

## Installation
1. Clone the repository
    ```sh
    git clone https://github.com/LeviSnoot/FNFest-Status.git
    cd FNFest-Status
    ```
2. *(Optional, but recommended)* Create a virtual environment
    ```sh
    python -m venv venv
    .\venv\Scripts\activate
    ```
3. Install the required dependencies
    ```sh
    pip install -r requirements.txt
    ```

## Usage

If you simply want a shell monitor of what is happening in Fortnite Festival, just run `playerStatus.py`
```sh
python .\playerStatus.py
```
If you additionally want to make use of the web app for display in OBS (or anywhere else), also start the web server after performing the previous step.

```sh
python .\web\app.py
```

If you have a service already running on port `5000`, make a copy of `config-example.ini`, rename it to `config.ini` and change the port value inside to whatever you'd like. You'll be able to access the web app at `http://127.0.0.1:<port-number>`.

The script currently works best if you start it after Fortnite has launched and you're in the lobby. I plan to make it work more robustly as a background service in future updates.

# Roadmap

- - [ ] Discord RPC implementation.
- - [ ] Cleaner launch procedure.

## Known issues
- Does not handle *multiplayer* Main Stage lobbies correctly. When I've inspected Fortnite's log file, I have been unable to find a reliable way to identify which player is the local player. Feel free to create a pull request if you have a solution. 

## Disclaimer

This project is not affiliated with, endorsed by, or in any way associated with Epic Games or Fortnite. All product names, trademarks, and registered trademarks are property of their respective owners.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.