from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import urllib.parse
import re

from PIL import Image, ImageOps
from io import BytesIO, BufferedReader


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

AUTH_URL = "https://api.spotify.com/v1/authorize"
REDIRECT_URL = "http://localhost:8000/callback"



def get_token():
    auth_string = CLIENT_ID + ":" + CLIENT_SECRET
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "authorization_code"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {'Authorization': 'Bearer ' + token}


def search_for_artist(artist_name, token):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f'?q={artist_name}&type=artist&limit=1'

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)['artists']['items']

    if len(json_result) == 0:
        print("No artist with this name exists...")
        return None
    return json_result[0]






def get_song_id_from_title(song_title, artist_name, token_info):
    params = {
        'q': f"{song_title} artist:{artist_name}", 
        'type': 'track',
        'limit': 1  # Limit the search to one result
    }
    headers = get_auth_header(token_info)
    response = get('https://api.spotify.com/v1/search', headers=headers, params=params)
    track_id = ""
    if response.status_code == 200:
        search_results = response.json()
        if 'tracks' in search_results and 'items' in search_results['tracks'] and len(search_results['tracks']['items']) > 0:
            track_id = search_results['tracks']['items'][0]['id']
            print(f"The Spotify ID for '{song_title}' is {track_id}")
            return track_id
        else:
            print(f"No matching tracks found for '{song_title}'")
    else:
        print(f"Failed to retrieve search results. Status Code: {response.status_code}")
        return




def parse_gpt_response_into_spotify_uris(gpt_output, token_info):
    print(gpt_output)
    track_ids = []
    for line in gpt_output.split('\n'):
        title, artist = line.split(' - ')
        artist_pattern = r'\s*(?:ft\.|featuring|feat\.|with).*$'
        cleaned_artist = re.sub(artist_pattern, '', artist, flags=re.IGNORECASE)
        id = get_song_id_from_title(title, cleaned_artist, token_info)
        if id:
            track_ids.append("spotify:track:" + id)
    return track_ids


def uris_to_playlist(uris, token, image_data):
    headers = get_auth_header(token)
    playlist_name = "Test"

    create_playlist_data = {
        "name": playlist_name,
        "public": False  # Change to True if you want the playlist to be public
    }
    print(f"TOKEN: {token}")
    sp = spotipy.Spotify(auth=token)
    user_id = sp.current_user()['id']
    print(user_id)

    create_playlist_response = post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=headers,
        data=json.dumps(create_playlist_data)
    )
    if not create_playlist_response.status_code == 201:
        print("Couldn't create playlist:", create_playlist_response.text)
    playlist_id = create_playlist_response.json()["id"]

    # Add tracks to playlist
    add_tracks_data = {"uris": uris}
    add_tracks_response = post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers=headers,
        data=json.dumps(add_tracks_data)
    )

    if add_tracks_response.status_code == 200 or add_tracks_response.status_code == 201:
        print("Playlist created successfully!")
        playlist_image = cleaned_playlist_image(image_data)
        sp.playlist_upload_cover_image(playlist_id, playlist_image)
    else:
        print("Couldn't add tracks to playlist:", add_tracks_response.status_code)
        return
    return playlist_id
    


def cleaned_playlist_image(image_data):
    if len(image_data) > 256000: # check if image is too big
        image = Image.open(BytesIO(base64.b64decode(image_data)))
        # Preserve EXIF orientation
        exif = image._getexif()
        if exif:
            orientation = exif.get(0x0112)
            image = ImageOps.exif_transpose(image)

        image = image.resize((300, 300))
        buffer = BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffer, format="JPEG")
        playlist_image = buffer.getvalue()
        image_data = base64.b64encode(playlist_image)
    return image_data