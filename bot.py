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
    print(f'Bot ID: {bot.user.id}')
    print('Bot is ready to receive commands!')
    
    # Get sp_dc token from environment variable
    sp_dc_token = os.getenv('SPOTIFY_SP_DC')
    if not sp_dc_token:
        print("WARNING: SPOTIFY_SP_DC environment variable not set!")
        print("The bot will not be able to authenticate with Spotify.")
        print("Bot will still start, but distributor commands will not work.")
    else:
        try:
            print("Attempting to authenticate with Spotify...")
            spotify_client = SpotifyClient(sp_dc_token)
            print("Successfully authenticated with Spotify!")
        except Exception as e:
            print(f"Failed to authenticate with Spotify: {e}")
            print("Bot will still start, but distributor commands will not work.")
            import traceback
            traceback.print_exc()


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
            # Detect if this is an album or track link
            is_album = '/album/' in spotify_link or spotify_link.startswith('spotify:album:')
            
            if is_album:
                # Handle album link
                album_id = spotify_client.extract_album_id_from_url(spotify_link)
                album_gid = spotify_client.id_to_gid(album_id)
                
                # Get album metadata
                album_metadata = spotify_client.get_album_metadata(album_gid)
                
                # Get distributor UUID from album
                track_uuid = None
                if isinstance(album_metadata, dict):
                    if 'licensor' in album_metadata and isinstance(album_metadata['licensor'], dict):
                        if 'uuid' in album_metadata['licensor']:
                            track_uuid = album_metadata['licensor']['uuid']
                            print(f"DEBUG: Found distributor UUID in album.licensor.uuid: {track_uuid}")
                
                # Extract album information
                album_name = album_metadata.get('name', 'Unknown')
                artists = album_metadata.get('artist', [])
                artist_names = ', '.join([a.get('name', '') for a in artists if isinstance(a, dict) and a.get('name')])
                if not artist_names:
                    artist_names = 'Unknown'
                label = album_metadata.get('label', 'Not Found')
                
                # Get UPC from album metadata
                upc = 'Not Found'
                import re
                album_str = str(album_metadata)
                upc_matches = re.findall(r'\b\d{12}\b', album_str)
                if upc_matches:
                    upc = upc_matches[0]
                
                # Get track count - check multiple possible locations
                track_count = 0
                print(f"DEBUG: Album metadata keys: {list(album_metadata.keys()) if isinstance(album_metadata, dict) else 'Not a dict'}")
                
                if 'tracks' in album_metadata:
                    tracks_data = album_metadata['tracks']
                    print(f"DEBUG: tracks field type: {type(tracks_data)}, value: {tracks_data}")
                    if isinstance(tracks_data, dict):
                        track_count = tracks_data.get('total', 0) or tracks_data.get('count', 0) or len(tracks_data.get('items', []))
                        print(f"DEBUG: tracks dict - total: {tracks_data.get('total')}, count: {tracks_data.get('count')}, items length: {len(tracks_data.get('items', []))}")
                    elif isinstance(tracks_data, list):
                        track_count = len(tracks_data)
                        print(f"DEBUG: tracks is list, length: {track_count}")
                
                # Try alternative field names if still 0
                if not track_count:
                    track_count = album_metadata.get('total_tracks', 0) or album_metadata.get('num_tracks', 0) or album_metadata.get('track_count', 0)
                    print(f"DEBUG: Trying alternative fields - total_tracks: {album_metadata.get('total_tracks')}, num_tracks: {album_metadata.get('num_tracks')}, track_count: {album_metadata.get('track_count')}")
                
                # Get album type (EP vs Album)
                album_type = album_metadata.get('type', 'Album').capitalize()
                # Sometimes it might be in album_group or other fields
                if album_type == 'Album' and 'album_group' in album_metadata:
                    album_group = album_metadata.get('album_group', '').capitalize()
                    if album_group:
                        album_type = album_group
                
                print(f"DEBUG: Final track count: {track_count}, Album type: {album_type}")
                
                # Get distributor
                distributor = 'Not Found'
                if track_uuid:
                    distributor = get_distributor(track_uuid) or 'Not Found'
                    
                    # Log unknown UUIDs to private channel
                    if distributor == 'Not Found':
                        log_channel_id = 1473480422695633057
                        try:
                            log_channel = bot.get_channel(log_channel_id)
                            if log_channel:
                                await log_channel.send(f"An unknown UUID was found: `{track_uuid}`\nLink: {spotify_link}")
                        except Exception as e:
                            print(f"DEBUG: Failed to log unknown UUID: {e}")
                
                # Create embed for album
                embed = discord.Embed(
                    title=album_name,
                    description=f"by **{artist_names}**" if artist_names != 'Unknown' else "",
                    color=0x1DB954  # Spotify green
                )
                
                embed.add_field(name="Type", value=album_type, inline=True)
                embed.add_field(name="Label", value=label, inline=True)
                embed.add_field(name="UPC", value=upc, inline=True)
                embed.add_field(name="Tracks", value=str(track_count) if track_count else "Unknown", inline=True)
                embed.add_field(name="Distributor", value=distributor, inline=False)
                
                await ctx.send(embed=embed)
                return
            
            # Handle track link (existing code)
            track_id = spotify_client.extract_track_id_from_url(spotify_link)
            
            # Convert to GID
            gid = spotify_client.id_to_gid(track_id)
            
            # Get track metadata
            metadata = spotify_client.get_track_metadata(gid)
            
            # Debug: Always log the metadata structure to see what we're working with
            print(f"DEBUG: Metadata response keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'Not a dict'}")
            print(f"DEBUG: Full metadata (first 1000 chars): {str(metadata)[:1000]}")
            
            # Extract UUID from metadata
            # The metadata response structure may vary - adjust based on actual API response
            track_uuid = None
            
            # Try different possible fields in the response
            if isinstance(metadata, dict):
                # The distributor UUID is in album.licensor.uuid
                if 'album' in metadata and isinstance(metadata['album'], dict):
                    album_data = metadata['album']
                    if 'licensor' in album_data and isinstance(album_data['licensor'], dict):
                        if 'uuid' in album_data['licensor']:
                            track_uuid = album_data['licensor']['uuid']
                            print(f"DEBUG: Found distributor UUID in album.licensor.uuid: {track_uuid}")
                        else:
                            print(f"DEBUG: album.licensor exists but no uuid field. Keys: {list(album_data['licensor'].keys())}")
                    else:
                        print(f"DEBUG: album exists but no licensor field. Album keys: {list(album_data.keys())}")
                else:
                    print(f"DEBUG: No album field in metadata. Top-level keys: {list(metadata.keys())}")
                
                # Fallback: if we still don't have the UUID, log for debugging
                if not track_uuid:
                    print(f"DEBUG: Could not find distributor UUID. Checking alternative fields...")
                    # Try other possible locations as fallback
                    if 'gid' in metadata:
                        print(f"DEBUG: Found track gid (not distributor UUID): {metadata['gid']}")
            
            # Extract track information for embed
            track_name = metadata.get('name', 'Unknown')
            artists = metadata.get('artist', [])
            artist_names = ', '.join([a.get('name', '') for a in artists if isinstance(a, dict) and a.get('name')])
            if not artist_names:
                artist_names = 'Unknown'
            
            album_data = metadata.get('album', {})
            album_name = album_data.get('name', 'Unknown') if isinstance(album_data, dict) else 'Unknown'
            label = album_data.get('label', 'Not Found') if isinstance(album_data, dict) else 'Not Found'
            
            # Get ISRC from track's external_id (ISRC is track-level)
            external_id = metadata.get('external_id', {})
            isrc = 'Not Found'
            if isinstance(external_id, dict):
                # Check if it's an ISRC
                if external_id.get('type') == 'isrc':
                    isrc = external_id.get('id', 'Not Found')
                # Sometimes it might be a list or different structure
            elif isinstance(external_id, list):
                # If it's a list, find the ISRC entry
                for ext_id in external_id:
                    if isinstance(ext_id, dict) and ext_id.get('type') == 'isrc':
                        isrc = ext_id.get('id', 'Not Found')
                        break
            
            # Get UPC from album metadata (UPC is album-level)
            upc = 'Not Found'
            if isinstance(album_data, dict) and 'gid' in album_data:
                # Get album GID and fetch full album metadata
                album_gid = album_data['gid']
                try:
                    print(f"DEBUG: Fetching album metadata for UPC, album GID: {album_gid}")
                    album_metadata = spotify_client.get_album_metadata(album_gid)
                    
                    # Log full album metadata structure for investigation
                    if isinstance(album_metadata, dict):
                        print(f"DEBUG: Full album metadata structure (first 2000 chars): {str(album_metadata)[:2000]}")
                        
                        # Try to extract UPC - check all possible locations
                        # Method 1: Direct fields
                        upc = album_metadata.get('upc') or album_metadata.get('upc_code') or album_metadata.get('barcode')
                        
                        # Method 2: Check external_id structure
                        if not upc or upc == 'Not Found':
                            album_ext_id = album_metadata.get('external_id', {})
                            if isinstance(album_ext_id, dict):
                                if album_ext_id.get('type') == 'upc':
                                    upc = album_ext_id.get('id', 'Not Found')
                            elif isinstance(album_ext_id, list):
                                for ext_id in album_ext_id:
                                    if isinstance(ext_id, dict) and ext_id.get('type') == 'upc':
                                        upc = ext_id.get('id', 'Not Found')
                                        break
                        
                        # Method 3: Check if UPC is nested elsewhere
                        if not upc or upc == 'Not Found':
                            # Check all string values that look like UPCs (12 digits)
                            import re
                            album_str = str(album_metadata)
                            upc_matches = re.findall(r'\b\d{12}\b', album_str)
                            if upc_matches:
                                print(f"DEBUG: Found potential UPCs in album metadata: {upc_matches}")
                                # Use first match (usually the UPC)
                                upc = upc_matches[0]
                        
                        print(f"DEBUG: Final UPC value: {upc}")
                except Exception as e:
                    print(f"DEBUG: Failed to fetch album metadata for UPC: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Get distributor
            distributor = 'Not Found'
            if track_uuid:
                distributor = get_distributor(track_uuid) or 'Not Found'
                
                # Log unknown UUIDs to private channel
                if distributor == 'Not Found':
                    log_channel_id = 1473480422695633057
                    try:
                        log_channel = bot.get_channel(log_channel_id)
                        if log_channel:
                            await log_channel.send(f"An unknown UUID was found: `{track_uuid}`\nLink: {spotify_link}")
                        else:
                            print(f"DEBUG: Could not find log channel {log_channel_id}")
                    except Exception as e:
                        print(f"DEBUG: Failed to log unknown UUID: {e}")
            else:
                # If we couldn't find UUID, show error in distributor field
                distributor = '❌ UUID not found'
            
            # Create embed
            embed = discord.Embed(
                title=track_name,
                description=f"by **{artist_names}**" if artist_names != 'Unknown' else "",
                color=0x1DB954  # Spotify green
            )
            
            # Add fields
            embed.add_field(name="Album", value=album_name, inline=False)
            embed.add_field(name="Label", value=label, inline=True)
            embed.add_field(name="ISRC", value=isrc, inline=True)
            embed.add_field(name="UPC", value=upc, inline=True)
            embed.add_field(name="Distributor", value=distributor, inline=False)
            
            await ctx.send(embed=embed)
                    
    except ValueError as e:
        await ctx.send(f"❌ Invalid Spotify URL: {e}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(f"Error in get_distributor_command: {e}")


def extract_spotify_link(text: str) -> str:
    """Extract Spotify link from text."""
    import re
    
    # Pattern for Spotify track URLs
    track_url_pattern = r'https?://(?:open\.)?spotify\.com(?:/intl-[^/]+)?/track/[a-zA-Z0-9]+'
    match = re.search(track_url_pattern, text)
    if match:
        return match.group(0)
    
    # Pattern for Spotify album URLs
    album_url_pattern = r'https?://(?:open\.)?spotify\.com(?:/intl-[^/]+)?/album/[a-zA-Z0-9]+'
    match = re.search(album_url_pattern, text)
    if match:
        return match.group(0)
    
    # Pattern for Spotify track URI
    track_uri_pattern = r'spotify:track:[a-zA-Z0-9]+'
    match = re.search(track_uri_pattern, text)
    if match:
        return match.group(0)
    
    # Pattern for Spotify album URI
    album_uri_pattern = r'spotify:album:[a-zA-Z0-9]+'
    match = re.search(album_uri_pattern, text)
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
        print("Please set DISCORD_BOT_TOKEN in Railway environment variables.")
        exit(1)
    
    print("Starting bot...")
    print("Note: Bot will start even if Spotify authentication fails.")
    
    # Optional: Enable keep-alive for Replit (prevents bot from sleeping)
    # Uncomment the next 2 lines if hosting on Replit free tier
    # from keep_alive import keep_alive
    # keep_alive()
    
    try:
        bot.run(discord_token)
    except Exception as e:
        print(f"Fatal error starting bot: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

