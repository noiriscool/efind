# Fixing GitHub Authentication

You're getting a 403 error because GitHub requires authentication. Here are quick fixes:

## Option 1: Use Personal Access Token (Easiest)

1. **Create a Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name it (e.g., "efind-bot")
   - Select scope: **`repo`** (full control of private repositories)
   - Click "Generate token"
   - **COPY THE TOKEN** (you won't see it again!)

2. **Use Token Instead of Password:**
   When you run `git push`, it will ask for:
   - **Username:** `noiriscool`
   - **Password:** Paste your token (not your GitHub password!)

## Option 2: Use SSH (More Permanent)

1. **Check if you have SSH key:**
   ```bash
   ls -la ~/.ssh
   ```

2. **If no key, generate one:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Press Enter twice for no passphrase (or set one)
   ```

3. **Add SSH key to GitHub:**
   ```bash
   # Copy your public key
   cat ~/.ssh/id_ed25519.pub
   # Copy the output
   ```
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the key, name it, save

4. **Change remote to SSH:**
   ```bash
   git remote set-url origin git@github.com:noiriscool/efind.git
   git push -u origin main
   ```

## Option 3: Use GitHub CLI (gh)

```bash
# Install if needed: brew install gh
gh auth login
# Follow prompts, select GitHub.com, HTTPS, authenticate in browser
git push -u origin main
```

## Quick Fix Right Now:

Just use Option 1 (Personal Access Token) - it's the fastest!

