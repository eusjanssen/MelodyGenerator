#!/usr/bin/env python3
"""
Flask backend for meditative MIDI generator.
Serves index.html and provides /api/generate which returns:
  {
    "midi_b64": "<base64-encoded-midi>",
    "melody": [ {start:beats, dur:beats, midi:, vel:} ... ],
    "chords": [ {start:beats, dur:beats, notes:[midi,..]} ... ],
    "seed": <seed>
  }

Run:
  pip install -r requirements.txt
  python app.py
"""
from flask import Flask, request, jsonify, send_from_directory, make_response
from io import BytesIO
import base64
import os
from midi_generator import generate_song_midi, generate_song_structure

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    body = request.get_json() or {}
    key = body.get('key', 'C')
    scale = body.get('scale', 'pentatonic')
    bars = int(body.get('bars', 8))
    bpm = int(body.get('bpm', 44))
    seed = body.get('seed', None)
    density = int(body.get('density', 1))
    # generate structure for playback and for MIDI
    structure = generate_song_structure(key=key, scale=scale, bars=bars, bpm=bpm, density=density, seed=seed)
    # generate midi bytes (Type=1 SMF)
    midi_bytes = generate_song_midi(structure)
    midi_b64 = base64.b64encode(midi_bytes).decode('ascii')
    response = {
        'midi_b64': midi_b64,
        'melody': structure['melody'],
        'chords': structure['chords'],
        'seed': structure['seed'],
        'markers': structure.get('markers', []),
        'bpm': bpm
    }
    return jsonify(response)

@app.route('/download/midi', methods=['POST'])
def download_midi():
    # optional direct download endpoint (multipart form or json same as /api/generate)
    body = request.get_json() or {}
    key = body.get('key', 'C')
    scale = body.get('scale', 'pentatonic')
    bars = int(body.get('bars', 8))
    bpm = int(body.get('bpm', 44))
    seed = body.get('seed', None)
    density = int(body.get('density', 1))
    structure = generate_song_structure(key=key, scale=scale, bars=bars, bpm=bpm, density=density, seed=seed)
    midi_bytes = generate_song_midi(structure)
    buf = BytesIO(midi_bytes)
    resp = make_response(buf.getvalue())
    resp.headers.set('Content-Type', 'audio/midi')
    fname = f"meditation_{structure['seed']}.mid"
    resp.headers.set('Content-Disposition', 'attachment', filename=fname)
    return resp

if __name__ == '__main__':
    # production: use gunicorn or similar. For development:
    app.run(host='0.0.0.0', port=5000, debug=True)
