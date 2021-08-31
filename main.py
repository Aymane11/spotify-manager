import os
import uuid
from pprint import pprint

import spotipy
from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   session)
from flask_session import Session

from models import *

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
	os.makedirs(caches_folder)

playlists = []
track_fields = [
	"items.added_by.id",
	"items.track.name",
	"items.track.external_urls.spotify",
	"items.track.album.name",
	"items.track.artists.name",
	"items.track.preview_url"
]
playlist_fields = [
	"id",
	"name",
	"description",
	"external_urls.spotify",
	"owner.id",
]


def session_cache_path():
	return caches_folder + session.get('uuid')


@app.errorhandler(500)
def internal_error(error):
	return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
	return render_template('errors/404.html'), 404


@app.route('/')
def index():
	if not session.get('uuid'):
		# Step 1. Visitor is unknown, give random ID
		session['uuid'] = str(uuid.uuid4())

	cache_handler = spotipy.cache_handler.CacheFileHandler(
		cache_path=session_cache_path())
	auth_manager = spotipy.oauth2.SpotifyOAuth(scope='playlist-modify-public playlist-modify-private playlist-read-private',
											   cache_handler=cache_handler,
											   show_dialog=True)

	if request.args.get("code"):
		# Step 3. Being redirected from Spotify auth page
		auth_manager.get_access_token(request.args.get("code"))
		return redirect('/')

	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		# Step 2. Display sign in link when no token
		auth_url = auth_manager.get_authorize_url()
		return render_template('home.html', auth_url=auth_url)

	# Step 4. Signed in, redirect to playlist list
	return redirect('/playlists')


@app.route('/sign_out')
def sign_out():
	try:
		# Remove the CACHE file (.cache-test) so that a new user can authorize.
		os.remove(session_cache_path())
		session.clear()
	except OSError as e:
		print("Error: %s - %s." % (e.filename, e.strerror))
	return redirect('/')


@app.route('/playlists')
def all_playlists():
	cache_handler = spotipy.cache_handler.CacheFileHandler(
		cache_path=session_cache_path())
	auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		return redirect('/')
	spotify = spotipy.Spotify(auth_manager=auth_manager)
	playlists = [Playlist(_id=playlist['id'], name=playlist['name'], description=playlist['description'], link=playlist['external_urls']['spotify'])
				 for playlist in spotify.current_user_playlists()['items'] if playlist['owner']['id'] == spotify.me()['id']]

	return render_template("playlists.html", name=spotify.me()["display_name"], playlists=playlists)


@app.route('/playlist/<playlist_id>')
def playlist(playlist_id):
	cache_handler = spotipy.cache_handler.CacheFileHandler(
		cache_path=session_cache_path())
	auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		return redirect('/')
	spotify = spotipy.Spotify(auth_manager=auth_manager)
	try:
		playlist = spotify.user_playlist(
			spotify.me()['id'], playlist_id, fields=','.join(playlist_fields))
		if playlist['owner']['id'] != spotify.me()['id']:
			return abort(404)
		playlist = Playlist(_id=playlist['id'], name=playlist['name'],
		         description=playlist['description'], link=playlist['external_urls']['spotify'])

		tracks = spotify.playlist_items(
			playlist_id, fields=','.join(track_fields))['items']

		track_list = []
		for track in tracks:
			name = track['track']['name']
			artists = [artist['name'] for artist in track['track']['artists']]
			album = track['track']['album']['name']
			user_id = track['added_by']['id']
			added_by = spotify.user(user_id)['display_name']
			preview_url = track['track']['preview_url']
			url = track['track']['external_urls']['spotify']
			track = Track(name=name, artists=artists, album=album,
						added_by=added_by, preview_url=preview_url, url=url)
			track_list.append(track)
		return render_template("tracks.html", tracks=track_list, playlist=playlist)
	except spotipy.client.SpotifyException:
		return abort(404)


@app.route('/change_order', methods=['POST'])
def change_order():
	cache_handler = spotipy.cache_handler.CacheFileHandler(
		cache_path=session_cache_path())
	auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		return redirect('/')
	spotify = spotipy.Spotify(auth_manager=auth_manager)
	pprint(request.form)
	playlist_id = request.form['playlist']
	try:
		playlist = spotify.user_playlist(
			spotify.me()['id'], playlist_id, fields=','.join(playlist_fields))
		if playlist['owner']['id'] != spotify.me()['id']:
			return abort(404)
		for move in request.form.getlist('moves[]'):
			src, dst = map(int, move.split('-'))
			if dst > src:
				dst += 1
			spotify.playlist_reorder_items(
				playlist_id, range_start=src, insert_before=dst)
		return jsonify({'html': "Done"})

	except spotipy.client.SpotifyException:
		return abort(404)


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
	app.run(threaded=True, port=8080, debug=True)
