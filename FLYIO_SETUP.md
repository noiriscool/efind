# Fly.io Setup (Free tier available)

Fly.io offers a free tier with good performance.

## Quick Setup:

1. **Install Fly CLI**
   ```bash
   # macOS
   curl -L https://fly.io/install.sh | sh
   
   # Or download from https://fly.io/docs/hands-on/install-flyctl/
   ```

2. **Sign Up**
   ```bash
   fly auth signup
   # Or go to fly.io and sign up, then:
   fly auth login
   ```

3. **Initialize Project**
   ```bash
   fly launch
   # Follow prompts - name your app, select region
   ```

4. **Create fly.toml** (if not auto-generated)
   - Fly should create this, but verify it has:
   ```toml
   app = "your-app-name"
   primary_region = "iad"  # or your preferred region
   
   [build]
   
   [env]
     DISCORD_BOT_TOKEN = "your_token_here"
     SPOTIFY_SP_DC = "your_cookie_here"
   ```

5. **Set Secrets**
   ```bash
   fly secrets set DISCORD_BOT_TOKEN=your_token
   fly secrets set SPOTIFY_SP_DC=your_cookie
   ```

6. **Deploy**
   ```bash
   fly deploy
   ```

## Free Tier:

- **3 shared-cpu VMs** (1GB RAM each)
- **3GB persistent volume storage**
- **160GB outbound data transfer**
- **Always on** - no sleeping!

## Note:

Fly.io is more CLI-focused. If you prefer a GUI, Railway or Render might be easier.

