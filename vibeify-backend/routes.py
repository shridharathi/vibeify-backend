import os
import time
import requests
from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from openai_service import call_gpt_with_image
from starlette.middleware.sessions import SessionMiddleware
from spotify_service import parse_gpt_response_into_spotify_uris, uris_to_playlist
from pydantic import BaseModel
from urllib.parse import urlencode
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import base64


app = FastAPI()


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

AUTH_URL = "https://accounts.spotify.com/authorize/?"
REDIRECT_URL = "http://localhost:8000/callback"
TOKEN_URL = "https://accounts.spotify.com/api/token"


app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)
app.token_info = {}

class ImageData(BaseModel):
    image: str

origins = [
    "http://localhost:3000",
    "localhost:3000",
    "https://vibeify.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = REDIRECT_URL,
        scope = "streaming user-read-email user-read-private user-library-read user-library-modify user-read-playback-state user-modify-playback-state playlist-modify-public playlist-modify-private ugc-image-upload",
        show_dialog=False
    )

def get_token():
    if not app.token_info:
        # If the token info is not found, redirect the user to the login route
        raise HTTPException(status_code=401, detail="User not logged in")
    # Check if the token is expired and refresh it if necessary
    now = int(time.time())
    is_expired = app.token_info['expires_in'] - now < 60
    if is_expired:
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': app.token_info['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()
        app.token_info = token_data
        #spotify_oauth = create_spotify_oauth()
        #app.token_info = spotify_oauth.refresh_access_token(app.token_info['refresh_token'])
    return app.token_info['access_token']



@app.get("/login")
async def login():
    #auth_url = create_spotify_oauth().get_authorize_url()
    #return RedirectResponse(auth_url)

    
    scope = "streaming user-read-email user-read-private user-library-read user-library-modify user-read-playback-state user-modify-playback-state playlist-modify-public playlist-modify-private ugc-image-upload"

    params = {
        'client_id' : CLIENT_ID,
        'response_type' : 'code',
        'scope' : scope,
        'redirect_uri' : REDIRECT_URL,
        'show_dialog' : True
    }

    auth_url = AUTH_URL + urlencode(params)
    return RedirectResponse(auth_url)
    


@app.get("/callback")
async def callback(request: Request):

    app.token_info = {}
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    # Exchange the authorization code for an access token and refresh token

    """
    token_info = create_spotify_oauth().get_access_token(code)
    app.token_info = token_info
    print(token_info)

    redirect_url = 'http://localhost:3000/handle-input?access_token=True'
    """

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URL,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    token_response = requests.post(TOKEN_URL, data=data)
    token_data = token_response.json()
    app.token_info = token_data
    #redirect_url = 'http://localhost:3000/handle-input?access_token=True'
    redirect_url = 'http://vibeify.netlify.app/handle-input?access_token=True'

    return RedirectResponse(url=redirect_url)
 

@app.post("/handle_image")
async def handle_image(data: ImageData, access_token: str = Depends(get_token)):
    gpt_output = call_gpt_with_image(data.image)
    uris = parse_gpt_response_into_spotify_uris(gpt_output, access_token)
    playlist_id = uris_to_playlist(uris, access_token, data.image)
    return {"answer": gpt_output, "playlist_id": playlist_id}

