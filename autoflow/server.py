"""
COMMON HTTP STATUS CODES:
200 - OK
201 - Created
400 - Bad Request
401 - Unauthorized
403 - Forbidden
404 - Not Found
405 - Method Not Allowed
409 - Conflict
418 - I'm a teapot ;) (RFC 2324 Hyper Text Coffee Pot Control Protocol)
500 - Internal Server Error
501 - Not Implemented
502 - Bad Gateway
503 - Service Unavailable
"""

import flask, io
from flask import Flask, send_file, Response, request, jsonify
import os, json, zipfile, sys, requests, base64, pickle, traceback
from time import time
from subprocess import Popen

from google.protobuf.json_format import MessageToJson

import numpy as np

from autoflow.core import Bars
from autoflow.parsing.syllabic import SyllableOverride, BASE_DIR
from autoflow.protos.python.bars_pb2 import WordProto

# TODO: server refactor based on functionality of loading bars etc. lol
# TODO: add artist, add song (when artist selected -- UI's job to ensure that), update song, etc.!!! :)

app = Flask(__name__)

"""
TODO:
- Change name and song txt to be JSON with fields that the client can choose what to do with as long as there's some base fields
"""

def _get_artists():
    return {artist : open(os.path.join(BASE_DIR, artist, "name.txt")).readline().strip() for artist in os.listdir(BASE_DIR) if artist[0] != "_"}

def _get_songs(artist):
    artist_base = os.path.join(BASE_DIR, artist)
    return {song : open(os.path.join(artist_base, song, "song.txt")).readline().strip() for song in os.listdir(artist_base) if os.path.isdir(os.path.join(artist_base, song)) and song[0] != "_"}
    
# TODO: autoflow specific dependencies

def _load_bars(artist, song):
    song_path = os.path.join(BASE_DIR, artist, song)
    return Bars(song_path)

@app.route("/")
def home():
    """Landing page"""
    return "Sup dog, welcome to Autoflow, where we rappin like it's automated, and these server's lights keep on like Vegas, and the bars so lava hot we turnin hog to bacon, so only God could save 'em, and the monsters made 'em, we ain't makin stars we way farther with the constellations"

@app.route("/get_artists", methods=['GET'])
def get_artists():
    """GET a list of all available artists
    """
    artist_names = _get_artists()

    response = {"artists": artist_names}

    return jsonify(response), 200

@app.route("/get_songs", methods=['GET'])
def get_songs():
    """GET a list of all annotated songs (maybe split into categories of your own vs other authors - study vs. creation)
    """
    artist_names = _get_artists()
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400

    songs = _get_songs(artist_req)
    response = {"artist": artist_names[artist_req], "songs": songs}

    return jsonify(response), 200

# TODO: Get song representation endpoint (can have simple parsing for now)
@app.route("/get_song", methods=['GET'])
def get_song():
    """GET song representation object (TODO: what exactly that looks like)
    """
    artist_names = _get_artists()
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    song_names = _get_songs(artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    bars = _load_bars(artist_req, song_req)

    # TODO: figure out best parsing structure... don't wanna over parse redundantly when you don't need to <-- lol

    response = {"artist": artist_names[artist_req], "song": song_names[song_req], "contents": bars.gen_lyrics(), "syllables": bars.gen_syllable_text()} # , "bars_proto" : MessageToJson(bars.to_proto())}

    # TODO: test speed of sending bytes over... likely faster than full json... protos are lightweight yeah
    # NOTE: this does just work though so we can keep devving on this while simultaneously trying to figure out the below being received

    return jsonify(response), 200

# MARK: Protobuf Serialization and Parsing: https://developers.google.com/protocol-buffers/docs/pythontutorial#parsing-and-serialization
@app.route("/get_song_proto", methods=['GET'])
def get_song_proto():
    """GET song protobuf representation object (ahahaaaa solved)
    """
    # TODO: helper function that takes in request and does all this to get bars yeesh (or sth idk)
    artist_names = _get_artists()
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    song_names = _get_songs(artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    bars = _load_bars(artist_req, song_req)

    return send_file(
        io.BytesIO(bars.to_proto().SerializeToString()),
        as_attachment=True,
        attachment_filename='bars.proto',
        mimetype='attachment/x-protobuf'
    )

# TODO: update local override endpoint - requires song and artist info (yeah this should def be a proto)
@app.route("/update_local_override", methods=['POST'])
def update_local_override():
    word_proto = WordProto()
    word_proto.ParseFromString(request.get_data())

    # TODO: turn this into helper function (make separate server file for this)

    artist_names = _get_artists()
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    song_names = _get_songs(artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    force = request.args.get('force') == "true"

    bars = _load_bars(artist_req, song_req)

    success = bars._local_override.add_override(word_proto.word, [syllable.syllable for syllable in word_proto.syllables], force)

    if success:
        return "Added to Local Override", 200
    else:
        return "Override already exists, check if user is sure to change", 300

# TODO: update global override endpoint - keep separate for now ye
@app.route("/update_global_override", methods=['POST'])
def update_global_override():
    word_proto = WordProto()
    word_proto.ParseFromString(request.get_data())

    force = request.args.get('force') == "true"

    success = SyllableOverride.global_override().add_override(word_proto.word, [syllable.syllable for syllable in word_proto.syllables], force)

    if success:
        return "Added to Local Override", 200
    else:
        return "Override already exists, check if user is sure to change", 300

@app.route("/update_song", methods=['POST'])
def update_song():
    return None, 501

@app.route("/push_annotations", methods=['POST'])
def push_annotations():
    # Get proto with annotations and spit out some stats lol idk (for now we can just write idk and maybe optionally load - can reset and stuff) --> ok to be hacky for a bit here
    return None, 501

@app.route("/analyze_song", methods=['GET'])
def get_bars():
    """GET song analysis results
    """
    artist_names = _get_artists()
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    song_names = _get_songs(artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    syllables = _load_bars(artist_req, song_req).gen_syllable_text()

    response = {"artist": artist_names[artist_req], "song": song_names[song_req], "syllables": syllables}

    return jsonify(response), 200

# TODO: Receive song representation endpoint (likely just endpoint split for now and then gets combined with...)
# TODO: Receive song update endpoint - syllabic annotations mainly for now
@app.route("/update_bars", methods=['POST'])
def update_bars():
    """POST song representation object update (TODO: version control + exactly what this looks like, syllabic annotations mainly for now)

    POST params:
    - New song or not (will do automated check but good to check for agreement)
    """
    return None, 501

