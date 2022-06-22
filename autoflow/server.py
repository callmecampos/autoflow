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
from autoflow.protos.python.bars_pb2 import SongProto, WordProto

# TODO: server refactor based on functionality of loading bars etc. lol
# TODO: add artist, add song (when artist selected -- UI's job to ensure that), update song, etc.!!! :)

app = Flask(__name__)

"""
TODO:
- Change name and song txt to be JSON with fields that the client can choose what to do with as long as there's some base fields
"""
    
# TODO: autoflow specific dependencies

@app.route("/")
def home():
    """Landing page"""
    return "Sup dog, welcome to Autoflow, where we rappin like it's automated, and these server's lights keep on like Vegas, and the bars so lava hot we turnin hog to bacon, so only God could save 'em, and the monsters made 'em, we ain't makin stars we way farther with the constellations"

@app.route("/get_artists", methods=['GET'])
def get_artists():
    """GET a list of all available artists
    """
    artist_names = Bars.get_artists(BASE_DIR)

    response = {"artists": artist_names}

    return jsonify(response), 200

@app.route("/get_songs", methods=['GET'])
def get_songs():
    """GET a list of all annotated songs (maybe split into categories of your own vs other authors - study vs. creation)
    """
    artist_names = Bars.get_artists(BASE_DIR)
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400

    songs = Bars.get_songs(BASE_DIR, artist_req)
    response = {"artist": artist_names[artist_req], "songs": songs}

    return jsonify(response), 200

# MARK: Protobuf Serialization and Parsing: https://developers.google.com/protocol-buffers/docs/pythontutorial#parsing-and-serialization
@app.route("/get_song_proto", methods=['GET'])
def get_song_proto():
    """GET song protobuf representation object (ahahaaaa solved)
    """
    # TODO: helper function that takes in request and does all this to get bars yeesh (or sth idk)
    artist_names = Bars.get_artists(BASE_DIR)
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    
    song_names = Bars.get_songs(BASE_DIR, artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    bars = Bars(BASE_DIR, artist_req, song_req)

    return send_file(
        io.BytesIO(bars.to_proto().SerializeToString()),
        as_attachment=True,
        attachment_filename='bars.proto',
        mimetype='attachment/x-protobuf'
    )

@app.route("/update_local_override", methods=['POST'])
def update_local_override():
    word_proto = WordProto()
    word_proto.ParseFromString(request.get_data())

    # TODO: turn this into helper function (make separate server file for this)

    artist_names = Bars.get_artists(BASE_DIR)
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    
    song_names = Bars.get_songs(BASE_DIR, artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    force = request.args.get('force') == "true"

    bars = Bars(BASE_DIR, artist_req, song_req)

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

@app.route("/update_song_proto", methods=['POST'])
def update_song():
    song_proto = SongProto()
    song_proto.ParseFromString(request.get_data()) # TODO: song proto should include artist and song (id and name...)

    # TODO: have this be a helper function in server_utils or sth

    artist_names = Bars.get_artists(BASE_DIR)
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    
    song_names = Bars.get_songs(BASE_DIR, artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    Bars.static_save_proto(BASE_DIR, artist_req, song_req, song_proto) # TODO: bars might want to just take artist_req / song_req? still need a way to get base_path with some static method, part of bars class

    """
    NOTE:
    - this will save the proto to file and make all other proto loads check proto when loading (even in stateless server)
    - this solves persistent bars and rhymes n shit... nice
    """

    return "OK", 200

@app.route("/push_annotations", methods=['POST'])
def push_annotations():
    # Get proto with annotations and spit out some stats lol idk (for now we can just write idk and maybe optionally load - can reset and stuff) --> ok to be hacky for a bit here
    return None, 501

# TODO: just pass proto back and forth lol -- might be slower but who cares?
@app.route("/analyze_song", methods=['GET'])
def get_bars():
    """GET song analysis results
    """
    artist_names = Bars.get_artists(BASE_DIR)
    
    artist_req = request.args.get('artist')
    if artist_req not in artist_names.keys():
        return "Artist does not exist", 400
    
    song_names = Bars.get_songs(BASE_DIR, artist_req)
    song_req = request.args.get('song')
    if song_req not in song_names.keys():
        return "Song does not exist", 500

    syllables = Bars(BASE_DIR, artist_req, song_req).to_proto().raw_syllables

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

