# DistroFinder Discord Bot

A Discord bot that identifies which distributor was used to release a track on Spotify.

## Features

- Accepts Spotify track links
- Converts Spotify track IDs to UUIDs
- Queries Spotify's metadata API
- Returns the distributor associated with the track (based on hardcoded mappings)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

You'll need:
- **DISCORD_BOT_TOKEN**: Get this from [Discord Developer Portal](https://discord.com/developers/applications)
- **SPOTIFY_SP_DC**: Get this from your browser cookies when logged into [Spotify Web Player](https://open.spotify.com/)
  - Open browser DevTools → Application → Cookies → `open.spotify.com`
  - Copy the value of the `sp_dc` cookie

### 3. Configure Distributor Mappings

Edit `distributors.py` and add your UUID → distributor mappings in the `DISTRIBUTOR_MAP` dictionary.

### 4. Run the Bot

```bash
python bot.py
```

Or with environment variables:

```bash
export DISCORD_BOT_TOKEN=your_token
export SPOTIFY_SP_DC=your_sp_dc
python bot.py
```

## Usage

In Discord, use the command:

```
!distributor <spotify_link>
```

Or just:

```
!distributor
```

And reply to a message containing a Spotify link.

Examples:
- `!distributor https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh`
- `!distributor spotify:track:4iV5W9uYEdYUVa79Axb7Rh`

## How It Works

1. Extracts the base62 track ID from the Spotify URL
2. Converts it to a hex GID (UUID) using base62 decoding
3. Queries Spotify's internal metadata API with the GID
4. Matches the UUID against hardcoded distributor mappings
5. Returns the distributor name

## Notes

- The TOTP implementation may need adjustment based on Spotify's actual requirements
- You'll need to manually populate the distributor mappings by associating UUIDs with distributor names
- The bot requires a valid `sp_dc` cookie token for authentication

