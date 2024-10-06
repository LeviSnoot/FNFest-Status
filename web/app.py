# Created by LeviSnoot
# https://github.com/LeviSnoot/FNFest-Status

from flask import Flask, jsonify, render_template
import multiprocessing
import json
import os
import signal
import sys
import time
import configparser

app = Flask(__name__)

# Path to the status file
status_file_path = os.path.join(os.path.dirname(__file__), '..', 'status.json')

# Path to the config file
config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

def read_status_from_file():
    with open(status_file_path, 'r') as f:
        return json.load(f)

def read_config_from_file():
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config

@app.route('/api/status')
def api_status():
    status = read_status_from_file()
    return jsonify(status)

@app.route('/')
def index():
    return render_template('index.html')

def run_flask(port):
    app.run(debug=True, use_reloader=False, port=port)

if __name__ == "__main__":
    config = read_config_from_file()
    port = config.getint('obswidget', 'port', fallback=5000)

    flask_process = multiprocessing.Process(target=run_flask, args=(port,))
    flask_process.start()

    def signal_handler(sig, frame):
        print('Stopping Flask server...')
        flask_process.terminate()
        flask_process.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep the main process running to handle signals
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)