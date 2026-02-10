import requests
import time
from totp import TOTP, TOTPGenerationException

TOKEN_URL = 'https://open.spotify.com/api/token'
SERVER_TIME_URL = 'https://open.spotify.com/api/server-time'  # Fixed: was /server-time, should be /api/server-time
SPOTIFY_HOME_PAGE_URL = "https://open.spotify.com/"
CLIENT_VERSION = "1.2.46.25.g7f189073"

HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US",
    "content-type": "application/json",
    "origin": SPOTIFY_HOME_PAGE_URL,
    "priority": "u=1, i",
    "referer": SPOTIFY_HOME_PAGE_URL,
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "spotify-app-version": CLIENT_VERSION,
    "app-platform": "WebPlayer",
}


class SpotifyClient:
    def __init__(self, dc_token: str) -> None:
        self.session = requests.Session()
        self.session.cookies.set('sp_dc', dc_token)
        self.session.headers.update(HEADERS)
        self.token = None
        # Try to login, but don't fail if it doesn't work
        # We might be able to use sp_dc cookie directly
        try:
            self.login()
        except Exception as e:
            print(f"WARNING: Could not get access token: {e}")
            print("Will attempt to use sp_dc cookie directly for API calls")

    def login(self):
        """Authenticate with Spotify using sp_dc token and TOTP."""
        try:
            # Try to get server time from Spotify
            server_time_response = self.session.get(SERVER_TIME_URL, timeout=10)
            
            # If 404, try alternative endpoint
            if server_time_response.status_code == 404:
                alt_url = 'https://open.spotify.com/server-time'
                server_time_response = self.session.get(alt_url, timeout=10)
            
            server_time_response.raise_for_status()
            server_time_data = server_time_response.json()
            
            # Debug: log the server time response
            print(f"DEBUG: Server time response: {server_time_data}")
            
            # Handle different response formats
            if "serverTime" in server_time_data:
                # Check if it's already in milliseconds or seconds
                server_time_raw = server_time_data["serverTime"]
                if server_time_raw > 1e12:  # Already in milliseconds
                    server_time = int(server_time_raw)
                else:  # In seconds, convert to milliseconds
                    server_time = int(server_time_raw * 1000)
            elif "timestamp" in server_time_data:
                server_time = int(server_time_data["timestamp"] * 1000)
            else:
                # Fallback to current time if server time not available
                server_time = int(time.time() * 1000)
                print("WARNING: Using local time as fallback for server time")
            
            print(f"DEBUG: Using server_time: {server_time}")
            
            # Generate TOTP using the custom implementation
            try:
                totp = TOTP()
                totp_value = totp.generate(server_time)
                totp_version = totp.version
                print(f"DEBUG: Generated TOTP: {totp_value}, version: {totp_version}")
            except TOTPGenerationException as e:
                raise Exception(f"Error generating TOTP: {e}")
            
            params = {
                "reason": "init",
                "productType": "web-player",
                "totp": totp_value,
                "totpVer": str(totp_version),
                "ts": str(server_time),
            }
            
            print(f"DEBUG: Auth params: {params}")
        except Exception as e:
            raise Exception(f"Error generating TOTP: {e}")
        
        try:
            req = self.session.get(TOKEN_URL, params=params, timeout=10)
            
            # Debug: log the response
            print(f"DEBUG: Token request status: {req.status_code}")
            if req.status_code != 200:
                print(f"DEBUG: Token request error response: {req.text[:500]}")
            
            req.raise_for_status()
            
            # Check if response is valid JSON
            try:
                token_data = req.json()
                print(f"DEBUG: Token response keys: {list(token_data.keys())}")
            except:
                raise Exception(f"Invalid JSON response from Spotify: {req.text[:200]}")
            
            if 'accessToken' not in token_data:
                raise Exception(f"Missing accessToken in response: {token_data}")
            
            self.token = token_data['accessToken']
            self.session.headers['authorization'] = f"Bearer {self.token}"
            print("DEBUG: Successfully authenticated with Spotify!")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during Spotify authentication: {e}")
        except Exception as e:
            raise Exception(f"sp_dc provided is invalid or authentication failed: {e}")

    def id_to_gid(self, base62_str: str) -> str:
        """Convert base62 string (Spotify track ID) to hex GID (UUID)."""
        characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        decimal_value = 0
        for char in base62_str:
            index = characters.find(char)
            if index == -1:
                raise ValueError("Invalid character in base62 string")
            decimal_value = decimal_value * 62 + index
        hex_value = hex(decimal_value)[2:].zfill(32)
        return hex_value

    def get_track_metadata(self, gid: str) -> dict:
        """Get track metadata from Spotify using GID."""
        url = f'https://spclient.wg.spotify.com/metadata/4/track/{gid}?market=from_token'
        
        # If we have a token, use it; otherwise try with just the cookie
        res = self.session.get(url)
        
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            # Token might be expired or invalid, try refreshing
            print("DEBUG: Got 401, token might be invalid. Response:", res.text[:200])
            raise Exception(f"Authentication failed: {res.status_code} - {res.text[:200]}")
        else:
            raise Exception(f"Failed to fetch track metadata: {res.status_code} - {res.text[:200]}")

    def extract_track_id_from_url(self, spotify_url: str) -> str:
        """Extract base62 track ID from Spotify URL."""
        # Handle various Spotify URL formats
        # https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh
        # https://spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh
        # spotify:track:4iV5W9uYEdYUVa79Axb7Rh
        
        if 'spotify.com/track/' in spotify_url:
            track_id = spotify_url.split('track/')[-1].split('?')[0]
        elif spotify_url.startswith('spotify:track:'):
            track_id = spotify_url.replace('spotify:track:', '')
        else:
            raise ValueError("Invalid Spotify URL format")
        
        return track_id

