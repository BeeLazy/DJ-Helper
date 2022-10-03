import re, glob, os
from os.path import getsize
from dotenv import load_dotenv
import urllib.request
import mp3
import discord
from discord.ext import commands
import wavelink
import asyncio

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
        f'{bot.user}(id:{bot.user.id}) connected to the following guild:\n'
        f'{guild.name}(id:{guild.id})'
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

# Converts milliseconds into a hour, minute, second tuple
async def timeTuple(ms: int):
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds = float(ms) / 1000
    return (hours, minutes, seconds)

# Events
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.id == bot.user.id:
        return

    msg_content = message.content.lower()

    # Delete messages with commands
    if message.content.startswith('!help'):
        print(f'Deleting user message {message.id}. Reason: Processed command')
        await message.delete()

    # Delete messages with forbidden words
    forbiddenWords = ['forbiddenwordsplaceholder1', 'forbiddenwordsplaceholder2']   
    if any(word in msg_content for word in forbiddenWords):
        print(f'Deleting user message {message.id}. Reason: Forbidden word')
        await message.author.send('Your message was deleted do to faul language')
        await message.delete()

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node: <{node.identifier}> is ready!')

@bot.event
async def on_wavelink_track_end(player: CustomPlayer, track: wavelink.Track, reason):
    if not player.queue.is_empty:
        next_track = player.queue.get()
        # Check that bot is in same voice channel as queuer
        # Should we follow the user if he have changed voice channel,
        # or contine to play where he was when it was queued? -> Create Follow option
        queuer = discord.utils.get(player.guild.members, id=next_track.info.get('QueuerId'))
        if not queuer.voice.channel.id == player.channel.id:
            print(f'Queuer is currently in voicechannel {queuer.voice.channel.name}')
            print(f'Bot is currently in voicechannel {player.channel.name}')
            print(f'Moving bot from {player.channel.name}(id:{player.channel.id}) to {queuer.voice.channel.name}(id:{queuer.voice.channel.id})')
            await player.move_to(bot.get_channel(queuer.voice.channel.id))
            # Without sleep, the next calls to play will pass old data in the ctx object
            while player.channel.id != queuer.voice.channel.id:
                await asyncio.sleep(0.1)
        await player.play(next_track)

@bot.event
async def on_wavelink_track_start(player: CustomPlayer, track: wavelink.Track):
    print(f'Started playing {track.title}')
    queuer = discord.utils.get(player.guild.members, id=player.track.info.get('QueuerId'))
    if queuer == None:
        queuer = await player.guild.fetch_member(player.track.info.get('QueuerId'))
        
    embed = discord.Embed(
        title=track.title,
        url=track.uri,
        description=f"Now playing {track.title}({track.duration}s) in <#{player.channel.id}> queued by <@{player.track.info.get('QueuerId')}> in <#{player.track.info.get('QueuerChannelId')}>"
    )
    embed.set_author(name=queuer.display_name, url=f'https://discordapp.com/users/{queuer.id}', icon_url=queuer.display_avatar)
    # Send the player update to the channel the song was queue in,
    # or send it to the channel the bot is playing the music in? -> Create Follow option
    #await player.channel.send(embed=embed)
    qc = bot.get_channel(player.track.info.get('QueuerChannelId'))
    await qc.send(embed=embed)

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
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

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
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    embed = discord.Embed(
        title='Bot information',
        description='Github: [DJ-Helper](https://github.com/BeeLazy/DJ-Helper)\n\nCreated by <@516598387773014029> - Powered by [Lavalink](https://github.com/freyacodes/Lavalink), [Wavelink](https://github.com/PythonistaGuild/Wavelink), [youtube-dl](https://github.com/ytdl-org/youtube-dl)',
        color=0x0066ff
    )
    await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

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
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if not vc:
        custom_player = CustomPlayer()
        vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)

    if vc.is_playing():
        search.info.update({'QueuerId': ctx.author.id, 'QueuerChannelId': ctx.channel.id})
        vc.queue.put(item=search)

        embed = discord.Embed(
            title=search.title,
            url=search.uri,
            description=f'<@{ctx.author.id}> queued {search.title}'
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
    else:
        search.info.update({'QueuerId': ctx.author.id, 'QueuerChannelId': ctx.channel.id})
        if not ctx.author.voice.channel.id == vc.channel.id:
            print(f'Queuer is currently in voicechannel {ctx.author.voice.channel.name}')
            print(f'Bot is currently in voicechannel {vc.channel.name}')
            print(f'Moving bot from {vc.channel.name}(id:{vc.channel.id}) to {ctx.author.voice.channel.name}(id:{ctx.author.voice.channel.id})')
            await vc.move_to(bot.get_channel(ctx.author.voice.channel.id))
            # Without sleep, the next calls to play will pass old data in the ctx object
            while vc.channel.id != ctx.author.voice.channel.id:
                await asyncio.sleep(0.1)
        await vc.play(search)

        embed = discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f'<@{ctx.author.id}> started playing {vc.source.title} in <#{vc.channel.id}>'
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)

@bot.command()
async def position(ctx, *, position: int=None):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if not vc.is_playing():
            return await ctx.send('Nothing is playing.')

        if position == None:
            print('Current position requested: [{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position)*1000)))
            embed = discord.Embed(
                title=vc.source.title,
                url=vc.source.uri,
                description=f'Playback position of {vc.source.title} is ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s].'.format(await timeTuple((vc.position)*1000)) +  f' Requested by <@{ctx.author.id}>'
            )
            embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
        else:
            print('New position requested: [{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000)))
            embed = discord.Embed(
                title=vc.source.title,
                url=vc.source.uri,
                description=f'<@{ctx.author.id}> changed playback position of {vc.source.title} to ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000))
            )
            embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
            await vc.seek((vc.position + position) * 1000)

        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.')

@bot.command()
async def seek(ctx, *, position: int=0):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if not vc.is_playing():
            return await ctx.send('Nothing is playing.')

        print('New position requested: [{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000)))
        embed = discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f'<@{ctx.author.id}> changed playback position of {vc.source.title} to ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000))
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
        await vc.seek((vc.position + position) * 1000)
        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.')

@bot.command()
async def skip(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

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
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

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
