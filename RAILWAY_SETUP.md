# Railway Setup (Free - $5/month credit)

Railway is reliable, easy to use, and has a generous free tier.

## Quick Setup (5 minutes):

1. **Sign Up**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub (easiest)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo" (if you have a repo)
   - OR select "Empty Project" (we'll upload files via CLI or dashboard)

3. **If Using GitHub (Recommended):**
   - Push your code to a GitHub repo
   - Connect the repo to Railway
   - Railway will auto-detect Python

4. **If Using Empty Project:**
   - Click "New" → "GitHub Repo" or "Empty Project"
   - If empty, you can upload files via Railway's dashboard or use Railway CLI

5. **Set Environment Variables**
   - In your project, click "Variables" tab
   - Add:
     - `DISCORD_BOT_TOKEN` = your Discord bot token
     - `SPOTIFY_SP_DC` = your Spotify sp_dc cookie

6. **Configure Build Settings**
   - Railway should auto-detect Python
   - If not, set:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python bot.py`

7. **Deploy**
   - Railway will automatically deploy
   - Check the "Deployments" tab for logs
   - Bot should be online! 🎉

## Railway CLI (Alternative Method):

If you prefer CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set variables
railway variables set DISCORD_BOT_TOKEN=your_token
railway variables set SPOTIFY_SP_DC=your_cookie

# Deploy
railway up
```

## Free Tier Details:

- **$5/month credit** (usually enough for a Discord bot)
- **No sleep** - bot stays online 24/7
- **Auto-deploys** on git push (if using GitHub)
- **Easy scaling** if needed

## Troubleshooting:

- **Build fails**: Check that `requirements.txt` is correct
- **Bot offline**: Check logs in Railway dashboard → Deployments
- **Out of credits**: Upgrade to paid or wait for monthly reset

