# Railway GitHub Connection Issues

If Railway can't find your repos, try these fixes:

## Fix 1: Configure GitHub App Permissions

1. In Railway, click "Configure GitHub App" (the gear icon)
2. This should open GitHub to authorize Railway
3. Make sure Railway has access to your repositories
4. Try searching again

## Fix 2: Authorize Railway on GitHub

1. Go to: https://github.com/settings/applications
2. Find "Railway" in the list
3. Click on it and check permissions
4. Make sure it has access to your repositories
5. If not listed, Railway will prompt you when you try to connect

## Fix 3: Use Empty Project + Connect Manually

1. In Railway, click "New Project"
2. Select "Empty Project" (not GitHub repo)
3. Once project is created, click "Settings"
4. Go to "Source" or "Connect Repo"
5. Try connecting your repo there

## Fix 4: Use Railway CLI (Most Reliable)

If the web UI isn't working, use the CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login (will open browser)
railway login

# Link to your project
railway link

# Or create new project
railway init

# Set variables
railway variables set DISCORD_BOT_TOKEN=your_token
railway variables set SPOTIFY_SP_DC=your_cookie

# Deploy
railway up
```

## Fix 5: Check Repository Visibility

Make sure your `efind` repo is:
- **Public**, OR
- **Private** but Railway has been granted access

If it's private, you may need to grant Railway access in GitHub settings.

