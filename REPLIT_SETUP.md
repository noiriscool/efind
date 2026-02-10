# Quick Replit Setup (5 minutes)

## Step-by-Step:

1. **Create Repl**
   - Go to [replit.com](https://replit.com)
   - Sign up/login (free)
   - Click "Create Repl" → Select "Python"
   - Name: `distrofinder-bot`

2. **Upload Files**
   - In Replit, click the "Files" icon (📁) in sidebar
   - Upload these files:
     - `bot.py`
     - `spotify_client.py`
     - `distributors.py`
     - `requirements.txt`
     - `keep_alive.py` (optional, for 24/7 uptime)

3. **Set Secrets (Environment Variables)**
   - Click the "Secrets" icon (🔒) in sidebar (or Tools → Secrets)
   - Click "New secret" and add:
     - **Key:** `DISCORD_BOT_TOKEN`
     - **Value:** Your Discord bot token
   - Click "New secret" again:
     - **Key:** `SPOTIFY_SP_DC`
     - **Value:** Your Spotify sp_dc cookie value

4. **Install Dependencies**
   - In the Replit shell (bottom panel), run:
   ```bash
   pip install -r requirements.txt
   ```

5. **Enable Keep-Alive (Optional but Recommended)**
   - Open `bot.py`
   - Find the lines at the bottom (around line 170):
   ```python
   # from keep_alive import keep_alive
   # keep_alive()
   ```
   - Uncomment them (remove the `#`):
   ```python
   from keep_alive import keep_alive
   keep_alive()
   ```

6. **Run the Bot**
   - Click the green "Run" button
   - You should see: `[Bot Name] has logged in!`
   - Bot is now online! 🎉

## Keep Bot Online 24/7 (Free)

Replit free tier sleeps after ~1 hour of inactivity. Options:

### Option A: UptimeRobot (Recommended)
1. Go to [uptimerobot.com](https://uptimerobot.com) (free account)
2. Add New Monitor:
   - Type: HTTP(s)
   - URL: Your Repl's URL (shown in Replit when running)
   - Monitoring Interval: 5 minutes
3. This will ping your bot every 5 minutes to keep it awake

### Option B: Use keep_alive.py
- Already enabled if you uncommented the lines above
- Creates a web server that responds to pings
- Still need UptimeRobot or similar to ping it

## Troubleshooting

- **"Module not found"**: Run `pip install -r requirements.txt` again
- **"Token invalid"**: Check your secrets are set correctly (case-sensitive)
- **Bot goes offline**: Enable keep-alive and set up UptimeRobot
- **Authentication fails**: Check your `SPOTIFY_SP_DC` value is correct

## Getting Your Tokens

### Discord Bot Token:
1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Create New Application → Name it
3. Go to "Bot" → Create Bot
4. Copy the token (click "Reset Token" if needed)
5. Enable "Message Content Intent" under Privileged Gateway Intents
6. Go to "OAuth2" → URL Generator → Select "bot" scope → Copy URL → Open in browser to invite bot

### Spotify sp_dc Cookie:
1. Open [open.spotify.com](https://open.spotify.com) in your browser
2. Log in
3. Open Developer Tools (F12)
4. Go to Application/Storage → Cookies → `https://open.spotify.com`
5. Find `sp_dc` cookie → Copy its value

