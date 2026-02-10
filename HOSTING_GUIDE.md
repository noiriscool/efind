# Quick Free Hosting Guide

## Option 1: Railway (Recommended - Best Free Tier) ⭐

### Steps:
1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo" (or "Empty Project")
3. If using GitHub: Push your code and connect the repo
4. Set environment variables in Railway dashboard:
   - `DISCORD_BOT_TOKEN`
   - `SPOTIFY_SP_DC`
5. Railway auto-detects Python and deploys
6. Bot stays online 24/7! (No sleeping on free tier)

**See `RAILWAY_SETUP.md` for detailed steps.**

---

## Option 2: Render (Free tier, may sleep)

### Steps:
1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
   - Or use "Empty Project" and connect via Railway CLI
3. Add environment variables:
   - `DISCORD_BOT_TOKEN`
   - `SPOTIFY_SP_DC`
4. Set start command: `python bot.py`
5. Deploy!

---

## Option 3: Render (Free tier, may sleep)

### Steps:
1. Go to [render.com](https://render.com) and sign up
2. Click "New" → "Web Service"
3. Connect your GitHub repo or upload files
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Add environment variables in the dashboard
6. Deploy!

**Note:** Free tier sleeps after inactivity. Use UptimeRobot to ping the service URL.

**See `RENDER_SETUP.md` for detailed steps.**

---

## Option 3: Fly.io (Free tier, always on)

### Steps:
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. Initialize: `fly launch`
4. Set secrets: `fly secrets set DISCORD_BOT_TOKEN=...`
5. Deploy: `fly deploy`

**See `FLYIO_SETUP.md` for detailed steps.**

---

## Recommendation

**Railway** is the best option:
- ✅ Easy GUI interface
- ✅ $5/month free credit (usually enough)
- ✅ No sleeping (stays online 24/7)
- ✅ Auto-deploys from GitHub
- ✅ Great for beginners

