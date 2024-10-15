let previousData = {
    current_song: '',
    current_artist: '',
    current_difficulty: '',
    current_album_art: '',
    current_instrument: '',
    current_intensity: -1,
    song_state: false,
    icon_bass: '',
    icon_guitar: '',
    icon_vocals: '',
    is_battle_stage: null,
    mode_name: '',
    round_number: 1
};

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const container = document.getElementById('container');
        const currentSong = document.getElementById('current_song');
        const currentArtist = document.getElementById('current_artist');
        const albumArt = document.getElementById('current_album_art');
        const instrumentIcon = document.getElementById('instrument_icon');
        const intensityIcon = document.getElementById('intensity_icon');
        const difficultyIcon = document.getElementById('difficulty_icon');
        const textInfo = document.getElementById('text_info');
        const instrumentName = document.getElementById('instrument_name');
        const modeName = document.getElementById('mode_name');
        const gameMode = document.getElementById('game_mode');
        const bsRound = document.getElementById('bs_round');
        const roundNumber = document.getElementById('round_number');

        if (data.song_state) {
            // Delay the visibility change to allow data to load
            setTimeout(() => {
                container.style.opacity = 1;
                textInfo.style.opacity = 1;
                albumArt.style.opacity = 1;
                instrumentIcon.style.opacity = 1;
                intensityIcon.style.opacity = 1;
                difficultyIcon.style.opacity = 1;
            }, 800); // Adjust the delay as needed
        } else {
            container.style.opacity = 0;
            textInfo.style.opacity = 0;
            albumArt.style.opacity = 0;
            instrumentIcon.style.opacity = 0;
            intensityIcon.style.opacity = 0;
            difficultyIcon.style.opacity = 0;
        }

        if (previousData.current_song !== data.current_song) {
            currentSong.parentElement.style.opacity = 0;
            currentSong.textContent = data.current_song || 'Song N/A';
            currentSong.parentElement.style.opacity = 1;
            previousData.current_song = data.current_song;
        }

        if (previousData.current_artist !== data.current_artist) {
            currentArtist.parentElement.style.opacity = 0;
            currentArtist.textContent = data.current_artist || 'Artist N/A';
            currentArtist.parentElement.style.opacity = 1;
            previousData.current_artist = data.current_artist;
        }

        if (previousData.current_difficulty !== data.current_difficulty) {
            let difficultySrc;
            switch (data.current_difficulty?.toLowerCase()) {
                case 'easy':
                    difficultySrc = '/static/assets/img/dif-0.png';
                    break;
                case 'medium':
                    difficultySrc = '/static/assets/img/dif-1.png';
                    break;
                case 'hard':
                    difficultySrc = '/static/assets/img/dif-2.png';
                    break;
                case 'expert':
                    difficultySrc = '/static/assets/img/dif-3.png';
                    break;
                default:
                    difficultySrc = '';
            }

            if (difficultySrc) {
                difficultyIcon.style.opacity = 0;
                difficultyIcon.src = difficultySrc;
                difficultyIcon.style.display = 'block';
                difficultyIcon.style.opacity = 1;
            } else {
                difficultyIcon.style.display = 'none';
            }
            previousData.current_difficulty = data.current_difficulty;
        }

        if (previousData.current_album_art !== data.current_album_art) {
            albumArt.style.opacity = 0;
            albumArt.src = data.current_album_art || '';
            albumArt.style.display = data.current_album_art ? 'block' : 'none';
            albumArt.style.opacity = 1;
            previousData.current_album_art = data.current_album_art;
        }

        let instrumentSrc;
        let instrumentText = '';
        switch (data.current_instrument?.toLowerCase()) {
            case 'bass':
                instrumentSrc = data.icon_bass === 'Keyboard' ? '/static/assets/img/keyboard.png' : '/static/assets/img/bass.png';
                instrumentText = data.icon_bass === 'Keyboard' ? 'Bass' : '';
                break;
            case 'drums':
                instrumentSrc = '/static/assets/img/drums.png';
                break;
            case 'lead':
                instrumentSrc = data.icon_guitar === 'Keyboard' ? '/static/assets/img/keyboard.png' : '/static/assets/img/lead.png';
                instrumentText = data.icon_guitar === 'Keyboard' ? 'Lead' : '';
                break;
            case 'vocals':
                instrumentSrc = data.icon_vocals === 'Keyboard' ? '/static/assets/img/keyboard.png' : '/static/assets/img/vocals.png';
                instrumentText = data.icon_vocals === 'Keyboard' ? 'Vocals' : '';
                break;
            case 'pro lead':
                instrumentSrc = data.icon_guitar === 'Keyboard' ? '/static/assets/img/pro_keyboard.png' : '/static/assets/img/pro_lead.png';
                instrumentText = data.icon_guitar === 'Keyboard' ? 'Pro Lead' : '';
                break;
            case 'pro bass':
                instrumentSrc = data.icon_bass === 'Keyboard' ? '/static/assets/img/pro_keyboard.png' : '/static/assets/img/pro_bass.png';
                instrumentText = data.icon_bass === 'Keyboard' ? 'Pro Bass' : '';
                break;
            default:
                instrumentSrc = '';
        }

        if (previousData.current_instrument !== data.current_instrument) {
            if (instrumentSrc) {
                instrumentIcon.style.opacity = 0;
                instrumentIcon.src = instrumentSrc;
                instrumentIcon.style.display = 'block';
                instrumentIcon.style.opacity = 1;
                if (instrumentText) {
                    instrumentName.textContent = instrumentText;
                    instrumentName.style.display = 'block';
                } else {
                    instrumentName.style.display = 'none';
                }
            } else {
                instrumentIcon.style.display = 'none';
                instrumentName.style.display = 'none';
            }
            previousData.current_instrument = data.current_instrument;
        } else if (!instrumentSrc) {
            instrumentIcon.style.display = 'none';
            instrumentName.style.display = 'none';
        }

        if (previousData.current_intensity !== data.current_intensity) {
            if (data.current_intensity !== null) {
                const intensitySrc = `/static/assets/img/int-${data.current_intensity}.png`;
                intensityIcon.style.opacity = 0;
                intensityIcon.src = intensitySrc;
                intensityIcon.style.display = 'block';
                intensityIcon.style.opacity = 1;
            } else {
                intensityIcon.style.display = 'none';
            }
            previousData.current_intensity = data.current_intensity;
        }

        // Update mode_name and game_mode visibility based on is_battle_stage
        if (previousData.is_battle_stage !== data.is_battle_stage) {
            bsRound.style.display = data.is_battle_stage ? 'block' : 'none';
            gameMode.style.display = data.is_battle_stage ? 'block' : 'none';
            previousData.is_battle_stage = data.is_battle_stage;
        }

        // Update round_number based on data.round_number
        if (previousData.round_number !== data.round_number) {
            roundNumber.textContent = data.round_number === 4 ? 'Final Round' : `Round ${data.round_number || 1}`;
            previousData.round_number = data.round_number;
        }

        previousData.song_state = data.song_state;
        previousData.icon_bass = data.icon_bass;
        previousData.icon_guitar = data.icon_guitar;
        previousData.icon_vocals = data.icon_vocals;

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

setInterval(fetchStatus, 1000);
fetchStatus();