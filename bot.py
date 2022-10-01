import re, glob, os
from os.path import getsize
from dotenv import load_dotenv
import urllib.request
import mp3
import discord
from discord.ext import commands
import wavelink

# Environment
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
GUILDID = os.getenv('DISCORD_GUILDID')
LAVALINKADDRESS = os.getenv('LAVALINK_ADDRESS')
LAVALINKPORT = os.getenv('LAVALINK_PORT')
LAVALINKPASSWORD = os.getenv('LAVALINK_PASSWORD')

# Client
intents = discord.Intents.all()
#intents = discord.Intents()
#intents.messages = True
#intents.message_content = True
#intents.reactions = False
#intents.members = False
#intents.guilds = False

bot = commands.Bot(command_prefix="!", intents=intents)

class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()

# HTTPS and websocket operations
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    bot.loop.create_task(connect_nodes())

    guild = bot.get_guild(GUILDID)
    if guild == None:
        print('Fetching guild...')
        guild = await bot.fetch_guild(GUILDID)

    print(
        f'{bot.user}(id: {bot.user.id}) connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

# Helper functions
async def connect_nodes():
    await bot.wait_until_ready()
    await wavelink.NodePool.create_node(
        bot=bot,
        host=LAVALINKADDRESS,
        port=LAVALINKPORT,
        password=LAVALINKPASSWORD
    )

# Events
@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node: <{node.identifier}> is ready!')

@bot.event
async def on_wavelink_track_end(player: CustomPlayer, track: wavelink.Track, reason):
    if not player.queue.is_empty:
        next_track = player.queue.get()
        await player.play(next_track)

# Commands
@bot.command()
async def connect(ctx):
    vc = ctx.voice_client # represents a discord voice connection
    try:
        channel = ctx.author.voice.channel
    except AttributeError:
        return await ctx.send('Please join a voice channel to connect.')

    if not vc:
        await ctx.author.voice.channel.connect(cls=CustomPlayer())
    else:
        await ctx.send('The bot is already connected to a voice channel')

@bot.command()
async def disconnect(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
    else:
        await ctx.send('The bot is not connected to a voice channel.')

@bot.command(
    aliases=['ytdl', 'dl', 'mp3'],
    description='Download mp3 file from a link or title search'
)
async def download(ctx, *, search: str=None):
    vc = ctx.voice_client
    if vc:
        if vc.is_playing() and not vc.is_paused():
            if ctx.message.content:
                msg = ctx.message.content
                await ctx.send(f'Got content:{msg}')
                if search:
                    print(f'We have some message content filtered:{search}')
                    # Avoid using message.content
                    msg = search
                    print(f'Message content: {msg} \n')

                    # regex to find url in the sent message
                    url = re.findall(r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', msg)
                    print(url)

                    if url:
                        # check if there are more than one links being sent
                        if (len(url) == 1):
                            validated_yt_url_1 = 'https://www.youtube.com/watch?v='
                            validated_yt_url_2 = 'https://youtu.be/'

                            if(validated_yt_url_1 in url[0] or validated_yt_url_2 in url[0]):
                                print('Youtube link is valid...')
                                await ctx.send(f'Downloading {url[0]}')
                                await mp3.song(url)
                                os.listdir()

                                # get all of the .mp3 file in this directory
                                for files in glob.glob('*.mp3'):

                                    # for each .mp3 file get the file size
                                    file_size = getsize(files)
                                    # convert the file size into an integer
                                    file_size = int(file_size)

                                    # check if the file size is over 8000000 bytes (discord limit for non bosted server's)
                                    if file_size > 8000000:
                                        print('The file size is over 8MB...\n')

                                        embed = discord.Embed(
                                            title='Error: Filesize over 8MB',
                                            description="Something went wrong :confused:\n\nTry sending a song that is under 7 minutes long, \nbecause of Discord's file size limit.\n\nCheck out !help and !info commands.",
                                            color=0x0066ff
                                        )
                                        await ctx.send(embed=embed)

                                        os.remove(files)
                                        print('File was removed')
                                    else:
                                        await ctx.send(file=discord.File(files))
                                        print('File was sent')

                                        os.remove(files)
                                        print('File was deleted')
                            else:
                                embed = discord.Embed(
                                    title='Error: Unsupported site',
                                    description="Something went wrong :confused: \n\nIt looks like you sent a link to an unsupported site.\n\nCheck out !help and !info commands.",
                                    color=0x0066ff
                                )
                                await ctx.send(embed=embed)
                                print('The link was not valid')
                        else:
                            embed = discord.Embed(
                                title='Error: More than one link',
                                description="Something went wrong :confused: \n\nIt looks like you sent more than one url's, please send one url at time.\n\nCheck out !help and !info commands.",
                                color=0x0066ff
                            )
                            await ctx.send(embed=embed)
                            print('There were more than one link')
                    elif not url:
                        # create a youtube search link with our search string
                        msg = msg.replace(' ', '+')
                        print(msg)
                        print(f'https://www.youtube.com/results?search_query={msg}')
                        html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={msg}')
                        video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())

                        # construct a new url from the videos id's we got back. Only first hit
                        new_url = 'https://www.youtube.com/watch?v=' + video_ids[0]
                        print(new_url)

                        await ctx.send(f'Downloading {new_url}')
                        await mp3.song([new_url])
                        os.listdir()

                        # get all of the .mp3 file in this directory
                        for files in glob.glob('*.mp3'):

                            # for each .mp3 file get the file size as integer
                            file_size = getsize(files)
                            file_size = int(file_size)

                            # check if the file size is over 8000000 bytes (discord limit for non bosted server's). See issue#2
                            if file_size > 8000000:
                                print('The file size is over 8MB')

                                embed = discord.Embed(
                                    title='Error: Filesize over 8MB',
                                    description="Something went wrong :confused:\n\nTry sending a song that is under 7 minutes long, \nbecause of Discord's file size limit.\n\nCheck out !help and !info commands.",
                                    color=0x0066ff
                                )
                                await ctx.send(embed=embed)

                                os.remove(files)
                                print('File was deleted')
                            else:
                                await ctx.send(file=discord.File(files))
                                print('File was sent')

                                os.remove(files)
                                print('File was deleted')
                    else:
                        embed = discord.Embed(
                            title='Error: General error',
                            description='Something went wrong check out examples in !help.',
                            color=0x0066ff
                        )
                        await ctx.send(embed=embed)
                else:
                    print('Nothing to search for. Searchword is required.')
            else:
                print('Error: No message content.')
        else:
            await ctx.send('Nothing is playing, so nothing to download.')
    else:
        await ctx.send('The bot is not connected to a voice channel')

@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title='Bot information',
        description='Github: [DJ-Helper](https://github.com/BeeLazy/DJ-Helper)\n\nCreated by <@516598387773014029> - Powered by [Lavalink](https://github.com/freyacodes/Lavalink), [Wavelink](https://github.com/PythonistaGuild/Wavelink), [youtube-dl](https://github.com/ytdl-org/youtube-dl)',
        color=0x0066ff
    )
    await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
    vc = ctx.voice_client
    if vc:
        if vc.is_playing() and not vc.is_paused():
            await vc.pause()
        else:
            await ctx.send('Nothing is playing.')
    else:
        await ctx.send('The bot is not connected to a voice channel.')

@bot.command()
async def play(ctx, *, search: wavelink.YouTubeTrack):
    vc = ctx.voice_client
    if not vc:
        custom_player = CustomPlayer()
        vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)

    if vc.is_playing():
        vc.queue.put(item=search)

        embed = discord.Embed(
            title=search.title,
            url=search.uri,
            description=f'<@{ctx.author.id}> queued {search.title} in <#{vc.channel.id}>'
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
    else:
        await vc.play(search)

        embed = discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f'<@{ctx.author.id}> started playing {vc.source.title} in <#{vc.channel.id}>'
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)

@bot.command()
async def skip(ctx):
    vc = ctx.voice_client
    if vc:
        if not vc.is_playing():
            return await ctx.send('Nothing is playing.')
        if vc.queue.is_empty:
            return await vc.stop()

        await vc.seek(vc.track.length * 1000)
        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.')

@bot.command()
async def resume(ctx):
    vc = ctx.voice_client
    if vc:
        if vc.is_paused():
            await vc.resume()
        else:
            await ctx.send('Nothing is paused.')
    else:
        await ctx.send('The bot is not connected to a voice channel')

# Error handling
@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Could not find a track.')
    else:
        await ctx.send('General error. Check that you are connected to a voice channel.')

# Execution
bot.run(TOKEN)
