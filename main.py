import os
import uuid

from dotenv import load_dotenv

import spotipy
from flask import Flask, abort, jsonify, redirect, render_template, request, session
from flask_session import Session

from models import *

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)

caches_folder = "./.spotify_caches/"
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get("uuid")


@app.before_request
def before_request():
    if not session.get("uuid"):
        # Visitor is unknown, give random ID
        session["uuid"] = str(uuid.uuid4())


@app.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def forbidden_error(error):
    return render_template("errors/403.html"), 403


def get_current_user(spotify):
    global current_user
    try:
        current_user
    except NameError:
        current_user = spotify.current_user()
        current_user = {
            "id": current_user["id"],
            "name": current_user["display_name"],
            "link": current_user["external_urls"]["spotify"],
        }
        current_user = User().from_dict(data=current_user)
    return current_user


@app.route("/")
def index():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-modify-public playlist-modify-private playlist-read-private",
        cache_handler=cache_handler,
        show_dialog=True,
    )

    if request.args.get("code"):
        # Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template("home.html", auth_url=auth_url)

    # Signed in, get user and redirect to playlist list
    current_user = get_current_user(spotipy.Spotify(auth_manager=auth_manager))
    return redirect("/playlists")


@app.route("/sign_out")
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect("/")


@app.route("/playlists")
def all_playlists():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    current_user = get_current_user(spotify)

    playlists = [
        playlist
        for playlist in spotify.current_user_playlists()["items"]
        if playlist["owner"]["id"] == current_user.id
    ]

    playlists = [Playlist().from_dict(playlist) for playlist in playlists]

    return render_template(
        "playlists.html", current_user=current_user, playlists=playlists
    )


@app.route("/playlist/<playlist_id>")
def playlist(playlist_id):
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    current_user = get_current_user(spotify)
    try:
        playlist = Playlist().from_dict(
            data=spotify.user_playlist(
                current_user.id, playlist_id, fields=",".join(PLAYLIST_FIELDS.values())
            )
        )

        if playlist.owner != current_user:
            return abort(403)

        playlist.owner = current_user
        response = spotify.playlist_items(
            playlist_id,
            fields=",".join(
                ["items." + field for field in TRACK_FIELDS.values()] + ["total"]
            ),
        )
        # Since spotify api limits the number of tracks to 100, we need to get the next page of tracks
        tracks = [Track().from_dict(data=track) for track in response["items"]]
        total = response["total"]
        while len(tracks) != total:
            response = spotify.playlist_items(
                playlist_id,
                offset=len(tracks),
                fields=",".join("items." + field for field in TRACK_FIELDS.values()),
            )
            tracks += [Track().from_dict(data=track) for track in response["items"]]

        playlist.add_tracks(tracks)

        return render_template("tracks.html", playlist=playlist)
    except spotipy.client.SpotifyException:
        return abort(500)


@app.route("/change_order", methods=["POST"])
def change_order():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    current_user = get_current_user(spotify)

    playlist_id = request.form["playlist"]
    try:
        playlist = Playlist().from_dict(
            data=spotify.user_playlist(
                current_user.id, playlist_id, fields=",".join(PLAYLIST_FIELDS.values())
            )
        )

        if playlist.owner != current_user:
            return abort(403)
        for move in request.form.getlist("moves[]"):
            src, dst = map(int, move.split("-"))
            if dst > src:
                dst += 1
            spotify.playlist_reorder_items(
                playlist_id, range_start=src, insert_before=dst
            )
        return jsonify({"html": "Done"})

    except spotipy.client.SpotifyException:
        return abort(500)


"""
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
"""
if __name__ == "__main__":
    app.run(threaded=True, port=8080, debug=True)
