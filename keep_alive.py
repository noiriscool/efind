"""
Keep-alive script for Replit to prevent the bot from sleeping.
Run this in a separate thread or use a service like UptimeRobot.
"""
from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Run the Flask server in a background thread."""
    t = Thread(target=run)
    t.daemon = True
    t.start()

if __name__ == '__main__':
    keep_alive()
    # Keep the script running
    while True:
        time.sleep(60)

