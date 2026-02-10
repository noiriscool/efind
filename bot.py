import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from spotify_client import SpotifyClient
from distributors import get_distributor

# Load environment variables from .env file
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Spotify client (will be set up in on_ready)
spotify_client = None


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    global spotify_client
    
    print(f'{bot.user} has logged in!')
    
    # Get sp_dc token from environment variable
    sp_dc_token = os.getenv('SPOTIFY_SP_DC')
    if not sp_dc_token:
        print("WARNING: SPOTIFY_SP_DC environment variable not set!")
        print("The bot will not be able to authenticate with Spotify.")
    else:
        try:
            spotify_client = SpotifyClient(sp_dc_token)
            print("Successfully authenticated with Spotify!")
        except Exception as e:
            print(f"Failed to authenticate with Spotify: {e}")


@bot.command(name='distributor', aliases=['distro', 'd'])
async def get_distributor_command(ctx, spotify_link: str = None):
    """
    Get the distributor for a Spotify track.
    
    Usage: !distributor <spotify_link>
    """
    if not spotify_client:
        await ctx.send("❌ Bot is not authenticated with Spotify. Please check configuration.")
        return
    
    # If no link provided, check if message has a Spotify link
    if not spotify_link:
        # Check if the command was invoked with a reply or check message content
        if ctx.message.reference:
            # Get the referenced message
            try:
                referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                # Look for Spotify links in the referenced message
                spotify_link = extract_spotify_link(referenced_msg.content)
            except:
                pass
        
        if not spotify_link:
            await ctx.send("❌ Please provide a Spotify link or reply to a message with a Spotify link.\n"
                          "Usage: `!distributor <spotify_link>`")
            return
    
    # Extract Spotify link if it's embedded in text
    if not spotify_link.startswith(('http', 'spotify:')):
        spotify_link = extract_spotify_link(spotify_link)
    
    if not spotify_link:
        await ctx.send("❌ Could not find a valid Spotify link.")
        return
    
    try:
        # Show typing indicator
        async with ctx.typing():
            # Extract track ID from URL
            track_id = spotify_client.extract_track_id_from_url(spotify_link)
            
            # Convert to GID
            gid = spotify_client.id_to_gid(track_id)
            
            # Get track metadata
            metadata = spotify_client.get_track_metadata(gid)
            
            # Extract UUID from metadata
            # The metadata response structure may vary - adjust based on actual API response
            track_uuid = None
            
            # Try different possible fields in the response
            if isinstance(metadata, dict):
                # Check for direct GID field
                if 'gid' in metadata:
                    track_uuid = metadata['gid']
                # Check for nested structure
                elif 'track' in metadata and isinstance(metadata['track'], dict):
                    if 'gid' in metadata['track']:
                        track_uuid = metadata['track']['gid']
                # Check for URI and extract UUID
                elif 'uri' in metadata:
                    uri = metadata['uri']
                    if 'spotify:track:' in uri:
                        # Extract and convert if needed
                        pass
                
                # Debug: print metadata structure if UUID not found
                if not track_uuid:
                    print(f"DEBUG: Metadata keys: {list(metadata.keys())}")
                    print(f"DEBUG: Full metadata: {metadata}")
            
            # Get distributor
            if track_uuid:
                distributor = get_distributor(track_uuid)
                if distributor:
                    await ctx.send(f"🎵 **Distributor:** {distributor}")
                else:
                    await ctx.send(f"❌ Distributor not found for this track.\n"
                                  f"UUID: `{track_uuid}`\n"
                                  f"Add this mapping to `distributors.py` if you know the distributor.")
            else:
                # Fallback: try using the GID directly
                distributor = get_distributor(gid)
                if distributor:
                    await ctx.send(f"🎵 **Distributor:** {distributor}")
                else:
                    await ctx.send(f"❌ Could not extract UUID from track metadata.\n"
                                  f"GID: `{gid}`\n"
                                  f"Please check the API response structure.")
                    
    except ValueError as e:
        await ctx.send(f"❌ Invalid Spotify URL: {e}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Error in get_distributor_command: {e}")


def extract_spotify_link(text: str) -> str:
    """Extract Spotify link from text."""
    import re
    
    # Pattern for Spotify URLs
    url_pattern = r'https?://(?:open\.)?spotify\.com/track/[a-zA-Z0-9]+'
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    
    # Pattern for Spotify URI
    uri_pattern = r'spotify:track:[a-zA-Z0-9]+'
    match = re.search(uri_pattern, text)
    if match:
        return match.group(0)
    
    return None


@bot.command(name='ping')
async def ping(ctx):
    """Check if the bot is responding."""
    await ctx.send('Pong! 🏓')


if __name__ == '__main__':
    # Get Discord bot token from environment variable
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if not discord_token:
        print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
        exit(1)
    
    # Optional: Enable keep-alive for Replit (prevents bot from sleeping)
    # Uncomment the next 2 lines if hosting on Replit free tier
    # from keep_alive import keep_alive
    # keep_alive()
    
    bot.run(discord_token)

