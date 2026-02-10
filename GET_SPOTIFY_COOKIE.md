# How to Get Your Spotify sp_dc Cookie

The `sp_dc` cookie is needed to authenticate with Spotify's API.

## Step-by-Step:

1. **Open Spotify Web Player**
   - Go to [open.spotify.com](https://open.spotify.com) in your browser
   - **Make sure you're logged in!**

2. **Open Developer Tools**
   - **Chrome/Edge:** Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - **Firefox:** Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - **Safari:** Enable Developer menu first (Preferences → Advanced → Show Develop menu), then `Cmd+Option+I`

3. **Go to Cookies/Storage**
   - Click the **"Application"** tab (Chrome/Edge) or **"Storage"** tab (Firefox)
   - In the left sidebar, expand **"Cookies"**
   - Click on **`https://open.spotify.com`**

4. **Find the sp_dc Cookie**
   - Look for a cookie named **`sp_dc`**
   - Click on it to see its value
   - **Copy the entire value** (it's a long string of characters)

5. **Use It**
   - Paste this value as your `SPOTIFY_SP_DC` environment variable in Railway

## Visual Guide:

```
Developer Tools
├── Application (or Storage)
    ├── Cookies
        └── https://open.spotify.com
            ├── sp_dc ← THIS ONE!
            ├── sp_key
            └── (other cookies)
```

## Important Notes:

- The cookie is **long** (usually 200+ characters)
- Make sure you copy the **entire value**
- The cookie expires after some time - if authentication fails later, get a fresh one
- Keep it **secret** - don't share it publicly (it's like a password)

## Troubleshooting:

- **Can't find sp_dc?** Make sure you're logged into Spotify web player
- **Cookie not there?** Try refreshing the page or logging out and back in
- **Value looks wrong?** Make sure you copied the entire value, not just part of it

