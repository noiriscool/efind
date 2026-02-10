# Render Setup (Free tier available)

Render is another solid option, though the free tier may sleep after inactivity.

## Quick Setup:

1. **Sign Up**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repo OR use "Public Git repository"
   - If no repo, you can use Render's dashboard to upload files

3. **Configure Service**
   - **Name:** `distrofinder-bot` (or any name)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

4. **Set Environment Variables**
   - Scroll to "Environment Variables"
   - Add:
     - `DISCORD_BOT_TOKEN` = your token
     - `SPOTIFY_SP_DC` = your cookie

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete
   - Check logs to see if bot started

## Free Tier Notes:

- **May sleep** after 15 minutes of inactivity
- **Wakes up** when receiving requests (but Discord bots don't receive HTTP requests)
- **Solution:** Use a service like UptimeRobot to ping the service URL every 5 minutes
- Or upgrade to paid ($7/month) for always-on

## Keep Free Tier Awake:

1. After deployment, copy your Render service URL (e.g., `https://distrofinder-bot.onrender.com`)
2. Set up [UptimeRobot](https://uptimerobot.com) to ping this URL every 5 minutes
3. Bot will stay awake!

