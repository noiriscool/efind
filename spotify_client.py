import requests
import time
import threading
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
        self.token_expires_at = None
        self.dc_token = dc_token
        self._refresh_thread = None
        self._stop_refresh = False
        # Try to login, but don't fail if it doesn't work
        # We might be able to use sp_dc cookie directly
        try:
            self.login()
            # Start background refresh loop (refresh every 7 minutes)
            self._start_refresh_loop()
        except Exception as e:
            print(f"WARNING: Could not get access token: {e}")
            print("Will attempt to use sp_dc cookie directly for API calls")
    
    def _start_refresh_loop(self):
        """Start a background thread that refreshes the session every 7 minutes."""
        def loop():
            while not self._stop_refresh:
                time.sleep(7 * 60)  # Sleep for 7 minutes
                if not self._stop_refresh:
                    try:
                        print("DEBUG: Background refresh loop - creating new session...")
                        self._new_session()
                        print("DEBUG: Background refresh successful")
                    except Exception as e:
                        print(f"DEBUG: Background refresh failed: {e}")
        
        self._refresh_thread = threading.Thread(target=loop, daemon=True)
        self._refresh_thread.start()
        print("DEBUG: Started background refresh loop (every 7 minutes)")
    
    def _new_session(self):
        """Create a completely new session - this is what fixes the expired token issue."""
        # Create a fresh session
        self.session = requests.Session()
        self.session.cookies.set('sp_dc', self.dc_token)
        self.session.headers.update(HEADERS)
        # Login to get new token
        self.login()
    
    def refresh_auth(self):
        """Refresh authentication by creating a new session."""
        try:
            # Create a completely new session instead of just refreshing token
            # This is what your friend's code does - _new_session()
            self._new_session()
            print("DEBUG: Successfully created new session")
            print(f"DEBUG: Token set: {bool(self.token)}")
            print(f"DEBUG: Authorization header: {self.session.headers.get('authorization', 'NOT SET')[:50]}...")
            print(f"DEBUG: sp_dc cookie present: {bool(self.session.cookies.get('sp_dc'))}")
        except Exception as e:
            print(f"WARNING: Failed to create new session: {e}")
            raise  # Re-raise so caller knows refresh failed

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
            # Store expiration time if provided
            if 'accessTokenExpirationTimestampMs' in token_data:
                self.token_expires_at = int(token_data['accessTokenExpirationTimestampMs'])
                print(f"DEBUG: Token expires at: {self.token_expires_at} (in {int((self.token_expires_at - time.time() * 1000) / 1000 / 60)} minutes)")
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

    def get_track_metadata(self, gid: str, retry_count: int = 3) -> dict:
        """Get track metadata from Spotify using GID."""
        url = f'https://spclient.wg.spotify.com/metadata/4/track/{gid}?market=from_token'
        
        # Check if token is expired or about to expire (within 15 minutes, or already expired)
        if self.token and self.token_expires_at:
            current_time_ms = int(time.time() * 1000)
            time_until_expiry = (self.token_expires_at - current_time_ms) / 1000 / 60  # minutes
            if time_until_expiry < 15:  # Refresh if expires within 15 minutes or already expired
                print(f"DEBUG: Token expires in {time_until_expiry:.1f} minutes, refreshing proactively...")
                try:
                    self.refresh_auth()
                    # Small delay after refresh to ensure it's propagated
                    time.sleep(0.5)
                except Exception as e:
                    print(f"DEBUG: Proactive refresh failed: {e}")
                    # If proactive refresh fails, we'll try again on 401
        elif not self.token:
            # No token at all, try to get one
            print("DEBUG: No token available, attempting to authenticate...")
            try:
                self.refresh_auth()
                time.sleep(0.5)
            except Exception as e:
                print(f"DEBUG: Initial authentication failed: {e}")
        
        for attempt in range(retry_count):
            try:
                # Add timeout and retry logic
                res = self.session.get(url, timeout=15)
                
                if res.status_code == 200:
                    return res.json()
                elif res.status_code == 401:
                    # Token might be expired, try to refresh
                    print(f"DEBUG: Got 401 on attempt {attempt + 1}, token may have expired. Refreshing...")
                    try:
                        # Try to refresh authentication
                        self.refresh_auth()
                        # Small delay to ensure new session is ready
                        time.sleep(0.5)
                        # Verify token was set
                        if not self.token:
                            raise Exception("Token refresh failed - no token set")
                        print(f"DEBUG: Token refreshed, retrying request with new token...")
                        # Verify everything is set before retrying
                        if not self.token:
                            raise Exception("Token refresh failed - no token set after refresh")
                        if not self.session.cookies.get('sp_dc'):
                            print("DEBUG: sp_dc cookie missing, re-setting...")
                            self.session.cookies.set('sp_dc', self.dc_token)
                        
                        sp_dc_value = self.session.cookies.get('sp_dc')
                        print(f"DEBUG: sp_dc cookie present: {bool(sp_dc_value)}, length: {len(sp_dc_value) if sp_dc_value else 0}")
                        
                        # Retry the request with new token
                        print(f"DEBUG: Retrying with fresh token and cookie...")
                        # Don't pass headers separately - session already has them updated
                        res = self.session.get(url, timeout=15)
                        if res.status_code == 200:
                            print(f"DEBUG: Successfully fetched metadata after token refresh")
                            return res.json()
                        elif res.status_code == 401:
                            # Still 401 after refresh - log detailed info
                            print(f"DEBUG: Still getting 401 after token refresh")
                            print(f"DEBUG: Response status: {res.status_code}")
                            print(f"DEBUG: Response headers: {dict(res.headers)}")
                            print(f"DEBUG: Response text: {res.text[:500]}")
                            print(f"DEBUG: Current token present: {bool(self.token)}")
                            print(f"DEBUG: Authorization header: {self.session.headers.get('authorization', 'NOT SET')[:50]}...")
                            sp_dc_cookie = self.session.cookies.get('sp_dc')
                            print(f"DEBUG: sp_dc cookie present: {bool(sp_dc_cookie)}, length: {len(sp_dc_cookie) if sp_dc_cookie else 0}")
                            print(f"DEBUG: Request URL: {url}")
                            print(f"DEBUG: Request headers sent: {dict(self.session.headers)}")
                            # Continue to next retry attempt instead of immediately failing
                            if attempt < retry_count - 1:
                                print(f"DEBUG: Will retry again (attempt {attempt + 2}/{retry_count})")
                                continue
                            else:
                                raise Exception(f"Authentication failed: 401 Unauthorized after {retry_count} attempts. Token refresh succeeded but metadata API still returns 401. Check Railway logs for details.")
                    except Exception as e:
                        error_msg = str(e)
                        # If it's our custom exception, re-raise it
                        if "Authentication failed" in error_msg or "Token refresh failed" in error_msg:
                            raise
                        print(f"DEBUG: Exception during token refresh: {e}")
                        # For other exceptions, continue to next retry
                        if attempt < retry_count - 1:
                            continue
                        else:
                            raise Exception(f"Failed to refresh token after {retry_count} attempts: {e}")
                elif res.status_code == 429:
                    # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"DEBUG: Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    if attempt == retry_count - 1:
                        raise Exception(f"Failed to fetch track metadata: {res.status_code} - {res.text[:200]}")
            except requests.exceptions.ConnectionError as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Connection error after {retry_count} attempts: {e}")
                print(f"DEBUG: Connection error on attempt {attempt + 1}, retrying...")
                time.sleep(1)
            except requests.exceptions.Timeout as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Request timed out after {retry_count} attempts: {e}")
                print(f"DEBUG: Timeout on attempt {attempt + 1}, retrying...")
                time.sleep(1)
        
        raise Exception("Failed to fetch track metadata after all retries")

    def get_album_metadata(self, album_gid: str, retry_count: int = 3) -> dict:
        """Get album metadata from Spotify using album GID."""
        url = f'https://spclient.wg.spotify.com/metadata/4/album/{album_gid}?market=from_token'
        
        # Check if token is expired or about to expire (within 15 minutes, or already expired)
        if self.token and self.token_expires_at:
            current_time_ms = int(time.time() * 1000)
            time_until_expiry = (self.token_expires_at - current_time_ms) / 1000 / 60  # minutes
            if time_until_expiry < 15:  # Refresh if expires within 15 minutes or already expired
                print(f"DEBUG: Token expires in {time_until_expiry:.1f} minutes, refreshing proactively...")
                try:
                    self.refresh_auth()
                    time.sleep(0.5)
                except Exception as e:
                    print(f"DEBUG: Proactive refresh failed: {e}")
        elif not self.token:
            print("DEBUG: No token available, attempting to authenticate...")
            try:
                self.refresh_auth()
                time.sleep(0.5)
            except Exception as e:
                print(f"DEBUG: Initial authentication failed: {e}")
        
        for attempt in range(retry_count):
            try:
                res = self.session.get(url, timeout=15)
                
                if res.status_code == 200:
                    album_data = res.json()
                    # Debug: Log album metadata structure to understand UPC location
                    print(f"DEBUG: Album metadata keys: {list(album_data.keys()) if isinstance(album_data, dict) else 'Not a dict'}")
                    if isinstance(album_data, dict):
                        # Log all possible UPC-related fields
                        print(f"DEBUG: Album has 'upc': {'upc' in album_data}")
                        print(f"DEBUG: Album has 'upc_code': {'upc_code' in album_data}")
                        print(f"DEBUG: Album has 'barcode': {'barcode' in album_data}")
                        print(f"DEBUG: Album has 'external_id': {'external_id' in album_data}")
                        if 'external_id' in album_data:
                            print(f"DEBUG: Album external_id type: {type(album_data['external_id'])}")
                            print(f"DEBUG: Album external_id value: {album_data['external_id']}")
                    return album_data
                elif res.status_code == 401:
                    print(f"DEBUG: Got 401 on album metadata, trying to refresh token...")
                    try:
                        self.refresh_auth()
                        time.sleep(0.5)
                        res = self.session.get(url, timeout=15)
                        if res.status_code == 200:
                            album_data = res.json()
                            print(f"DEBUG: Album metadata keys after refresh: {list(album_data.keys()) if isinstance(album_data, dict) else 'Not a dict'}")
                            return album_data
                    except Exception as e:
                        print(f"DEBUG: Failed to refresh token for album: {e}")
                    
                    if attempt == retry_count - 1:
                        raise Exception(f"Authentication failed: 401 Unauthorized for album metadata")
                else:
                    if attempt == retry_count - 1:
                        raise Exception(f"Failed to fetch album metadata: {res.status_code} - {res.text[:200]}")
            except requests.exceptions.ConnectionError as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Connection error after {retry_count} attempts: {e}")
                time.sleep(1)
            except requests.exceptions.Timeout as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Request timed out after {retry_count} attempts: {e}")
                time.sleep(1)
        
        raise Exception("Failed to fetch album metadata after all retries")
    
    def get_artist_metadata(self, artist_gid: str, retry_count: int = 3) -> dict:
        """Get artist metadata from Spotify using artist GID."""
        url = f'https://spclient.wg.spotify.com/metadata/4/artist/{artist_gid}?market=from_token'
        
        # Check if token is expired or about to expire
        if self.token and self.token_expires_at:
            current_time_ms = int(time.time() * 1000)
            time_until_expiry = (self.token_expires_at - current_time_ms) / 1000 / 60
            if time_until_expiry < 15:
                try:
                    self.refresh_auth()
                    time.sleep(0.5)
                except Exception as e:
                    print(f"DEBUG: Proactive refresh failed: {e}")
        elif not self.token:
            try:
                self.refresh_auth()
                time.sleep(0.5)
            except Exception as e:
                print(f"DEBUG: Initial authentication failed: {e}")
        
        for attempt in range(retry_count):
            try:
                res = self.session.get(url, timeout=15)
                
                if res.status_code == 200:
                    return res.json()
                elif res.status_code == 401:
                    try:
                        self.refresh_auth()
                        time.sleep(0.5)
                        res = self.session.get(url, timeout=15)
                        if res.status_code == 200:
                            return res.json()
                    except Exception as e:
                        print(f"DEBUG: Failed to refresh token for artist: {e}")
                    
                    if attempt == retry_count - 1:
                        raise Exception(f"Authentication failed: 401 Unauthorized for artist metadata")
                else:
                    if attempt == retry_count - 1:
                        raise Exception(f"Failed to fetch artist metadata: {res.status_code} - {res.text[:200]}")
            except requests.exceptions.ConnectionError as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Connection error after {retry_count} attempts: {e}")
                time.sleep(1)
            except requests.exceptions.Timeout as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Request timed out after {retry_count} attempts: {e}")
                time.sleep(1)
        
        raise Exception("Failed to fetch artist metadata after all retries")
    
    def get_artist_albums(self, artist_gid: str, retry_count: int = 3) -> list:
        """Get all albums for an artist. Returns list of album GIDs."""
        # First get artist metadata to see album structure
        artist_metadata = self.get_artist_metadata(artist_gid)
        
        # Debug: Log the structure
        print(f"DEBUG: Artist metadata keys: {list(artist_metadata.keys()) if isinstance(artist_metadata, dict) else 'Not a dict'}")
        
        albums = []
        
        # Check ALL group fields: album_group, single_group, appears_on_group
        # These might contain different types of releases
        group_fields = ['album_group', 'single_group', 'appears_on_group']
        
        for field_name in group_fields:
            if field_name in artist_metadata:
                group_data = artist_metadata[field_name]
                print(f"DEBUG: {field_name} type: {type(group_data)}, value: {str(group_data)[:500]}")
                
                if isinstance(group_data, list):
                    for group in group_data:
                        if isinstance(group, dict) and 'album' in group:
                            albums_data = group['album']
                            if isinstance(albums_data, list):
                                for album in albums_data:
                                    if isinstance(album, dict) and 'gid' in album:
                                        if album['gid'] not in albums:
                                            albums.append(album['gid'])
                            elif isinstance(albums_data, dict) and 'gid' in albums_data:
                                if albums_data['gid'] not in albums:
                                    albums.append(albums_data['gid'])
        
        # Also check direct 'albums' field
        if 'albums' in artist_metadata:
            albums_data = artist_metadata['albums']
            print(f"DEBUG: albums field type: {type(albums_data)}, value: {str(albums_data)[:500]}")
            if isinstance(albums_data, list):
                for album in albums_data:
                    if isinstance(album, dict) and 'gid' in album:
                        if album['gid'] not in albums:
                            albums.append(album['gid'])
            elif isinstance(albums_data, dict):
                # Check for pagination
                if 'items' in albums_data:
                    print(f"DEBUG: Found 'items' in albums dict, count: {len(albums_data.get('items', []))}")
                    for album in albums_data['items']:
                        if isinstance(album, dict) and 'gid' in album:
                            if album['gid'] not in albums:
                                albums.append(album['gid'])
                # Check for total count to see if we're missing albums
                if 'total' in albums_data:
                    total = albums_data.get('total', 0)
                    print(f"DEBUG: Total albums according to API: {total}, found so far: {len(albums)}")
                elif 'gid' in albums_data:
                    if albums_data['gid'] not in albums:
                        albums.append(albums_data['gid'])
        
        print(f"DEBUG: Found {len(albums)} albums from metadata groups")
        
        # Use the artist albums endpoint with pagination as PRIMARY method
        # This endpoint should return all albums, not just a limited set
        all_albums_from_endpoint = []
        
        # Try multiple possible endpoints - need to find the right one that returns ALL albums
        # Also try with different query parameters for pagination
        endpoints_to_try = [
            # Try browse API with different parameters
            f'https://spclient.wg.spotify.com/browse/v1/artist/{artist_gid}/albums?market=from_token&limit=50&offset=0',
            f'https://spclient.wg.spotify.com/browse/v1/artist/{artist_gid}/albums?market=from_token',
            # Try artistview with pagination
            f'https://spclient.wg.spotify.com/artistview/v1/artist/{artist_gid}/albums?offset=0&limit=50&market=from_token',
            f'https://spclient.wg.spotify.com/artistview/v1/artist/{artist_gid}/albums?market=from_token',
            # Try entity-view endpoints
            f'https://spclient.wg.spotify.com/artist-entity-view/v2/spotify/artist/{artist_gid}/albums?market=from_token&limit=50',
            f'https://spclient.wg.spotify.com/artist-entity-view/v2/spotify/artist/{artist_gid}/albums?market=from_token',
            # Try releases endpoints
            f'https://spclient.wg.spotify.com/artist-entity-view/v2/spotify/artist/{artist_gid}/releases/all?market=from_token&limit=50',
            f'https://spclient.wg.spotify.com/artist-entity-view/v2/spotify/artist/{artist_gid}/releases?market=from_token&limit=50',
        ]
        
        for endpoint_url in endpoints_to_try:
            try:
                print(f"DEBUG: Trying endpoint: {endpoint_url}")
                
                # Check token
                if self.token and self.token_expires_at:
                    current_time_ms = int(time.time() * 1000)
                    time_until_expiry = (self.token_expires_at - current_time_ms) / 1000 / 60
                    if time_until_expiry < 15:
                        try:
                            self.refresh_auth()
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"DEBUG: Proactive refresh failed: {e}")
                
                res = self.session.get(endpoint_url, timeout=15)
                print(f"DEBUG: Endpoint response status: {res.status_code}")
                
                if res.status_code == 200:
                    data = res.json()
                    print(f"DEBUG: Endpoint response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    print(f"DEBUG: Endpoint response (first 1000 chars): {str(data)[:1000]}")
                    
                    # Check various possible structures
                    releases = []
                    if isinstance(data, dict):
                        if 'releases' in data:
                            releases = data['releases']
                        elif 'items' in data:
                            releases = data['items']
                        elif 'albums' in data:
                            releases = data['albums']
                        elif 'data' in data:
                            releases = data['data']
                    elif isinstance(data, list):
                        releases = data
                    
                    if isinstance(releases, list) and len(releases) > 0:
                        print(f"DEBUG: Found {len(releases)} releases/albums in response")
                        for release in releases:
                            if isinstance(release, dict):
                                # Get album GID from various possible locations
                                album_gid = None
                                if 'gid' in release:
                                    album_gid = release['gid']
                                elif 'album' in release:
                                    if isinstance(release['album'], dict) and 'gid' in release['album']:
                                        album_gid = release['album']['gid']
                                    elif isinstance(release['album'], str):
                                        # Might be a GID string
                                        album_gid = release['album']
                                elif 'uri' in release:
                                    # Extract from URI like spotify:album:...
                                    uri = release['uri']
                                    if 'album:' in uri:
                                        album_id = uri.split('album:')[-1]
                                        album_gid = self.id_to_gid(album_id)
                                
                                if album_gid and album_gid not in all_albums_from_endpoint:
                                    all_albums_from_endpoint.append(album_gid)
                        
                        # Check if there's pagination - if total > current count, fetch more pages
                        total_available = None
                        if isinstance(data, dict):
                            total_available = data.get('total') or data.get('count')
                            has_more = data.get('next') is not None or data.get('has_more', False)
                            print(f"DEBUG: Total available: {total_available}, found so far: {len(all_albums_from_endpoint)}, has_more: {has_more}")
                            
                            # If there are more pages, try to fetch them
                            if has_more and total_available and total_available > len(all_albums_from_endpoint):
                                offset = len(all_albums_from_endpoint)
                                limit = 50
                                while len(all_albums_from_endpoint) < total_available:
                                    paginated_url = f"{endpoint_url.split('?')[0]}?offset={offset}&limit={limit}&market=from_token"
                                    print(f"DEBUG: Fetching page at offset {offset}")
                                    try:
                                        page_res = self.session.get(paginated_url, timeout=15)
                                        if page_res.status_code == 200:
                                            page_data = page_res.json()
                                            page_releases = []
                                            if isinstance(page_data, dict):
                                                page_releases = page_data.get('releases') or page_data.get('items') or page_data.get('albums') or page_data.get('data') or []
                                            elif isinstance(page_data, list):
                                                page_releases = page_data
                                            
                                            if len(page_releases) == 0:
                                                break
                                            
                                            for release in page_releases:
                                                if isinstance(release, dict):
                                                    album_gid = None
                                                    if 'gid' in release:
                                                        album_gid = release['gid']
                                                    elif 'album' in release and isinstance(release['album'], dict) and 'gid' in release['album']:
                                                        album_gid = release['album']['gid']
                                                    elif 'uri' in release and 'album:' in release['uri']:
                                                        album_id = release['uri'].split('album:')[-1]
                                                        album_gid = self.id_to_gid(album_id)
                                                    
                                                    if album_gid and album_gid not in all_albums_from_endpoint:
                                                        all_albums_from_endpoint.append(album_gid)
                                            
                                            offset += limit
                                            time.sleep(0.2)
                                        else:
                                            break
                                    except Exception as e:
                                        print(f"DEBUG: Error fetching paginated results: {e}")
                                        break
                        
                        # If we found albums, use this endpoint and break
                        if len(all_albums_from_endpoint) > 0:
                            print(f"DEBUG: Successfully found {len(all_albums_from_endpoint)} albums from endpoint")
                            albums = all_albums_from_endpoint  # Replace with endpoint results
                            break
                elif res.status_code == 404:
                    print(f"DEBUG: Endpoint returned 404, trying next endpoint")
                    continue
                else:
                    print(f"DEBUG: Endpoint returned {res.status_code}: {res.text[:200]}")
                    continue
            except Exception as e:
                print(f"DEBUG: Error with endpoint {endpoint_url}: {e}")
                continue
        
        # If we didn't get albums from endpoints, merge with metadata results
        if len(all_albums_from_endpoint) == 0:
            print(f"DEBUG: No albums from endpoints, using metadata results: {len(albums)} albums")
            # Merge any albums we found from metadata
            for album_gid in albums:
                if album_gid not in all_albums_from_endpoint:
                    all_albums_from_endpoint.append(album_gid)
            albums = all_albums_from_endpoint
        
        print(f"DEBUG: Final album count: {len(albums)}")
        return albums

    def extract_track_id_from_url(self, spotify_url: str) -> str:
        """Extract base62 track ID from Spotify URL."""
        # Handle various Spotify URL formats:
        # https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh
        # https://open.spotify.com/intl-it/track/4iV5W9uYEdYUVa79Axb7Rh (international)
        # https://spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh
        # spotify:track:4iV5W9uYEdYUVa79Axb7Rh
        
        # Handle international URLs with /intl-XX/ path
        if '/intl-' in spotify_url and '/track/' in spotify_url:
            # Extract track ID from international URL
            # Format: .../intl-XX/track/TRACK_ID
            track_id = spotify_url.split('/track/')[-1].split('?')[0]
        elif 'spotify.com/track/' in spotify_url:
            # Standard URL format
            track_id = spotify_url.split('track/')[-1].split('?')[0]
        elif spotify_url.startswith('spotify:track:'):
            # URI format
            track_id = spotify_url.replace('spotify:track:', '')
        else:
            raise ValueError("Invalid Spotify track URL format")
        
        # Validate track ID (should be base62 characters)
        if not track_id or not all(c.isalnum() for c in track_id):
            raise ValueError(f"Invalid track ID format: {track_id}")
        
        return track_id
    
    def extract_album_id_from_url(self, spotify_url: str) -> str:
        """Extract base62 album ID from Spotify URL."""
        # Handle various Spotify album URL formats:
        # https://open.spotify.com/album/4iV5W9uYEdYUVa79Axb7Rh
        # https://open.spotify.com/intl-it/album/4iV5W9uYEdYUVa79Axb7Rh (international)
        # https://spotify.com/album/4iV5W9uYEdYUVa79Axb7Rh
        # spotify:album:4iV5W9uYEdYUVa79Axb7Rh
        
        # Handle international URLs with /intl-XX/ path
        if '/intl-' in spotify_url and '/album/' in spotify_url:
            album_id = spotify_url.split('/album/')[-1].split('?')[0]
        elif 'spotify.com/album/' in spotify_url:
            album_id = spotify_url.split('album/')[-1].split('?')[0]
        elif spotify_url.startswith('spotify:album:'):
            album_id = spotify_url.replace('spotify:album:', '')
        else:
            raise ValueError("Invalid Spotify album URL format")
        
        # Validate album ID (should be base62 characters)
        if not album_id or not all(c.isalnum() for c in album_id):
            raise ValueError(f"Invalid album ID format: {album_id}")
        
        return album_id
    
    def extract_artist_id_from_url(self, spotify_url: str) -> str:
        """Extract base62 artist ID from Spotify URL."""
        # Handle various Spotify artist URL formats:
        # https://open.spotify.com/artist/4iV5W9uYEdYUVa79Axb7Rh
        # https://open.spotify.com/intl-it/artist/4iV5W9uYEdYUVa79Axb7Rh (international)
        # https://spotify.com/artist/4iV5W9uYEdYUVa79Axb7Rh
        # spotify:artist:4iV5W9uYEdYUVa79Axb7Rh
        
        # Handle international URLs with /intl-XX/ path
        if '/intl-' in spotify_url and '/artist/' in spotify_url:
            artist_id = spotify_url.split('/artist/')[-1].split('?')[0]
        elif 'spotify.com/artist/' in spotify_url:
            artist_id = spotify_url.split('artist/')[-1].split('?')[0]
        elif spotify_url.startswith('spotify:artist:'):
            artist_id = spotify_url.replace('spotify:artist:', '')
        else:
            raise ValueError("Invalid Spotify artist URL format")
        
        # Validate artist ID (should be base62 characters)
        if not artist_id or not all(c.isalnum() for c in artist_id):
            raise ValueError(f"Invalid artist ID format: {artist_id}")
        
        return artist_id

