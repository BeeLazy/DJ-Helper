import re, glob, os
from os.path import getsize
from dotenv import load_dotenv
import urllib.request
from mp3 import ytd
import discord
from discord.ext import commands
from discord.ui import View, Button
import wavelink
import asyncio
from dbox import DBox
from dropbox.exceptions import AuthError

# Environment
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LAVALINKADDRESS = os.getenv('LAVALINK_ADDRESS')
LAVALINKPORT = os.getenv('LAVALINK_PORT')
LAVALINKPASSWORD = os.getenv('LAVALINK_PASSWORD')
DROPBOXTOKEN = os.getenv('DROPBOX_TOKEN')

# Discord Client
intents = discord.Intents.all()
#intents = discord.Intents()
#intents.messages = True
#intents.message_content = True
#intents.reactions = False
#intents.members = False
#intents.guilds = False

class CustomBot(commands.Bot):
    def __init__(self, **kargs):
        super().__init__(**kargs)
        self.embedded_players = dict()

bot = CustomBot(command_prefix=commands.when_mentioned_or('!'), intents=intents)

class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()

# Dropbox client
dBox = DBox(DROPBOXTOKEN, bot)

# HTTPS and websocket operations
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    bot.loop.create_task(connect_nodes())

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

# Classes
class DownloadButton(Button):
    def __init__(self, view, label):
        super().__init__(label=label, style=discord.ButtonStyle.green, custom_id=label)
        self.aview = view

    async def callback(self, interaction):
        self.label = f'Processing {self.label}'
        self.disabled = True
        self.style = discord.ButtonStyle.blurple
        await interaction.response.edit_message(view=self.aview)
        await download(interaction, search=interaction.message.embeds[0].url)

class LinkButton(Button):
    def __init__(self, view, label, url):
        super().__init__(label=label, style=discord.ButtonStyle.url, url=url)
        self.aview = view
        self.url = url

# Views
class EmbeddedPlayerView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    async def on_timeout(self):
        await self.ctx.send('Timeout')

    async def error_handler(self, error, item, interaction):
        print(str(error))
        await interaction.response.send_message(str(error))

# Events
@bot.event
async def on_download_start(ctx, url):
    print('Entered on_download_start')
    print(f'Requested url:{url}')

@bot.event
async def on_download_end(ctx, url):
    print("Entered on_download_end")
    print(f'Requested url:{url}')
    print(f'Destination path:TODO')

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
async def on_upload_start(ctx, path):
    print('Entered on_upload_start')
    print(f'Source path:{path}')

@bot.event
async def on_upload_end(ctx, uri):
    print("Entered on_upload_end")
    # Check if interaction, or if download has been called directly
    if type(ctx) is commands.context.Context:
        print('User called download directly')
        await ctx.send(f'Starting download of {uri}')
    elif type(ctx) is discord.interactions.Interaction:
        print(f'Result(Shared link or destination path):{uri}')
        if uri == 'Embedded':
            # Update embedded player
            ep = bot.embedded_players.get(ctx.guild.id)
            embeddedPlayerChannel = bot.get_channel(ep[0])
            embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
            view = View.from_message(embeddedPlayer)
            buttonType = ctx.data.get('custom_id')
            buttonOld = [x for x in view.children if x.label==f'Processing {buttonType}'][0]
            view.remove_item(buttonOld)
            buttonNew = DownloadButton(view, f'{buttonType} Embedded')
            buttonNew.disabled = True
            view.add_item(buttonNew)
            await embeddedPlayer.edit(view=view)
        elif uri == 'TooBig':
            # Update embedded player
            ep = bot.embedded_players.get(ctx.guild.id)
            embeddedPlayerChannel = bot.get_channel(ep[0])
            embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
            view = View.from_message(embeddedPlayer)
            buttonType = ctx.data.get('custom_id')
            buttonOld = [x for x in view.children if x.label==f'Processing {buttonType}'][0]
            view.remove_item(buttonOld)
            buttonNew = DownloadButton(view, f'{buttonType} too big')
            buttonNew.style = discord.ButtonStyle.red
            buttonNew.disabled = True
            view.add_item(buttonNew)
            await embeddedPlayer.edit(view=view)
        else:
            # Update embedded player
            ep = bot.embedded_players.get(ctx.guild.id)
            embeddedPlayerChannel = bot.get_channel(ep[0])
            embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
            view = View.from_message(embeddedPlayer)
            buttonType = ctx.data.get('custom_id')
            buttonOld = [x for x in view.children if x.label==f'Processing {buttonType}'][0]
            view.remove_item(buttonOld)
            buttonNew = LinkButton(view, f'{buttonType}', uri)
            view.add_item(buttonNew)
            await embeddedPlayer.edit(view=view)
    else:
        print(f'Unknown type {type(ctx)} of ctx in on_upload_end')

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

        # Delete embedded player
        ep = bot.embedded_players.get(player.guild.id)
        embeddedPlayerChannel = bot.get_channel(ep[0])
        embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
        await embeddedPlayer.delete()
    else:
        # Update embedded player
        embed = discord.Embed(
            title='Playlist has concluded',
            url='https://github.com/BeeLazy/DJ-Helper',
            description='Thank you for using DJ-Helper!'
        )
        embed.set_author(name=bot.user.display_name, url=f'https://discordapp.com/users/{bot.user.id}', icon_url=bot.user.display_avatar)

        ep = bot.embedded_players.get(player.guild.id)
        embeddedPlayerChannel = bot.get_channel(ep[0])
        embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
        await embeddedPlayer.edit(embed=embed, view=None, delete_after=300)

@bot.event
async def on_wavelink_track_start(player: CustomPlayer, track: wavelink.Track):
    print(f'Started playing {track.title}')
    queuer = discord.utils.get(player.guild.members, id=player.track.info.get('QueuerId'))
    if queuer == None:
        queuer = await player.guild.fetch_member(player.track.info.get('QueuerId'))
    
    view = EmbeddedPlayerView(player)
    newButton = DownloadButton(view, 'MP3')
    view.add_item(newButton)
    embed = discord.Embed(
        title=track.title,
        url=track.uri,
        description=f"Now playing {track.title}({track.duration}s) in <#{player.channel.id}> queued by <@{player.track.info.get('QueuerId')}> in <#{player.track.info.get('QueuerChannelId')}>"
    )
    embed.set_author(name=queuer.display_name, url=f'https://discordapp.com/users/{queuer.id}', icon_url=queuer.display_avatar)
    # Send the player update to the channel the song was queue in,
    # or send it to the channel the bot is playing the music in? -> Create Follow option
    #await player.channel.send(embed=embed)
    #qc = bot.get_channel(player.track.info.get('QueuerChannelId'))
    #await qc.send(embed=embed)
    #
    #ep = bot.embedded_players.get(player.guild.id)
    #embeddedPlayerChannel = bot.get_channel(ep[0])
    #embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
    #await embeddedPlayer.edit(embed=embed, view=view)
    queuerChannel = bot.get_channel(player.track.info.get('QueuerChannelId'))
    sent_message = await queuerChannel.send(embed=embed, view=view)
    bot.embedded_players.update({player.guild.id : [queuerChannel.id, sent_message.id]})

# Commands
@bot.command()
async def connect(ctx):
    vc = ctx.voice_client # represents a discord voice connection
    try:
        channel = ctx.author.voice.channel
    except AttributeError:
        return await ctx.send('Please join a voice channel to connect.', delete_after=30)

    if not vc:
        await ctx.author.voice.channel.connect(cls=CustomPlayer())
    else:
        await ctx.send('The bot is already connected to a voice channel.', delete_after=30)

@bot.command()
async def disconnect(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
    else:
        await ctx.send('The bot is not connected to a voice channel.', delete_after=30)

@bot.command(
    aliases=['ytdl', 'dl', 'mp3'],
    description='Download mp3 file from a link or title search'
)
async def download(ctx, *, search: str=None):
    # Bot calling function after user response button callback
    if ctx.message.author.id != bot.user.id:
        print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
        await ctx.message.delete()

    if search:
        # regex to find url in the sent message
        url = re.findall(r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', search)
        print(url)

        if url:
            # check if there are more than one links being sent
            if (len(url) == 1):
                validated_yt_url_1 = 'https://www.youtube.com/watch?v='
                validated_yt_url_2 = 'https://youtu.be/'

                if(validated_yt_url_1 in url[0] or validated_yt_url_2 in url[0]):
                    print('Youtube link is valid')
                    # Create embedded downloader
                    embed = discord.Embed(
                        title=search,
                        url=url[0],
                        description=f'<@{ctx.user.id}> requested download of {search}({url[0]}) in <#{ctx.channel.id}>'
                    )
                    embed.set_author(name=ctx.user.display_name, url=f'https://discordapp.com/users/{ctx.user.id}', icon_url=ctx.user.display_avatar)
                    embedded_downloader = await ctx.channel.send(embed=embed)

                    ytd_result = ytd(bot)
                    await ytd_result.song(ctx, url)
                    os.listdir()

                    # get all of the .mp3 file in this directory
                    for files in glob.glob('*.mp3'):

                        # for each .mp3 file get the file size as integer
                        file_size = getsize(files)
                        file_size = int(file_size)

                        # Files over 350MB are not allowed. Limit in upload_file
                        if file_size > 350000000:
                            print('The file size is over 350MB')
                            embed = discord.Embed(
                                title='Error: Filesize over 350MB',
                                url=url[0],
                                description="Something went wrong :confused:\n\nTry sending a song that is not this huge!\n\nThe maximum size allowed for conversion is 350MB.\n\nCheck out !help and !info commands.",
                                color=0x0066ff
                            )
                            await embedded_downloader.edit(embed=embed, delete_after=30)

                            os.remove(files)
                            print('File was deleted')
                        # Check if the file size is over 8MB (Discord limit for non bosted server's). See issue#2
                        # Upload to Dropbox and share link
                        elif file_size > 8000000:
                            print('The file size is 8MB-350MB')
                            file_to = f'/{files}'
                            print(f'Uploading {files} to Dropbox')
                            link = dBox.upload_file_with_link(ctx=ctx, file_from=files, file_to=file_to)
                            print(f'Created shared link {link}')
                            
                            embed = discord.Embed(
                                title=files,
                                url=link,
                                description=f'File has been converted to MP3\n\n[Download it here]({link})',
                                color=0x0066ff
                            )
                            await embedded_downloader.edit(embed=embed, delete_after=3600)

                            os.remove(files)
                            print('File was deleted')
                        # Send as attachment to channel
                        else:
                            print('The file size is under 8MB')
                            bot.dispatch('upload_start', ctx, files)
                            embed = discord.Embed(
                                title=files,
                                url=url[0],
                                description=f'File has been converted to MP3 and embedded',
                                color=0x0066ff
                            )
                            await embedded_downloader.add_files(discord.File(files))
                            await embedded_downloader.edit(embed=embed, delete_after=3600)
                            print('File was sent')
                            bot.dispatch('upload_end', ctx, 'Embedded')

                            os.remove(files)
                            print('File was deleted')
                else:
                    embed = discord.Embed(
                        title='Error: Unsupported site',
                        description="Something went wrong :confused: \n\nIt looks like you sent a link to an unsupported site.\n\nCheck out !help and !info commands.",
                        color=0x0066ff
                    )
                    await ctx.channel.send(embed=embed, delete_after=30)
                    print('The link was not valid')
            else:
                embed = discord.Embed(
                    title='Error: More than one link',
                    description="Something went wrong :confused: \n\nIt looks like you sent more than one url's, please send one url at time.\n\nCheck out !help and !info commands.",
                    color=0x0066ff
                )
                await ctx.channel.send(embed=embed, delete_after=30)
                print('There were more than one link')
        elif not url:
            # create a youtube search link with our search string
            search = search.replace(' ', '+')
            print(search)
            print(f'https://www.youtube.com/results?search_query={search}')
            html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={search}')
            video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())

            # construct a new url from the videos id's we got back. Only first hit
            new_url = 'https://www.youtube.com/watch?v=' + video_ids[0]
            print(new_url)

            # Create embedded downloader
            embed = discord.Embed(
                title=search,
                url=new_url,
                description=f'<@{ctx.user.id}> requested download of {search}({new_url}) in <#{ctx.channel.id}>'
            )
            embed.set_author(name=ctx.user.display_name, url=f'https://discordapp.com/users/{ctx.user.id}', icon_url=ctx.user.display_avatar)
            embedded_downloader = await ctx.channel.send(embed=embed)
            
            ytd_result = ytd(bot)
            await ytd_result.song(ctx, [new_url])
            os.listdir()

            # get all of the .mp3 file in this directory
            for files in glob.glob('*.mp3'):

                # for each .mp3 file get the file size as integer
                file_size = getsize(files)
                file_size = int(file_size)

                # Files over 350MB are not allowed. Limit in upload_file
                if file_size > 350000000:
                    print('The file size is over 350MB')
                    embed = discord.Embed(
                        title='Error: Filesize over 350MB',
                        url=new_url,
                        description="Something went wrong :confused:\n\nTry sending a song that is not this huge!\n\nThe maximum size allowed for conversion is 350MB.\n\nCheck out !help and !info commands.",
                        color=0x0066ff
                    )
                    await embedded_downloader.edit(embed=embed, delete_after=30)

                    os.remove(files)
                    print('File was deleted')
                # Check if the file size is over 8MB (Discord limit for non bosted server's). See issue#2
                # Upload to Dropbox and share link
                elif file_size > 8000000:
                    print('The file size is 8MB-350MB')
                    file_to = f'/{files}'
                    print(f'Uploading {files} to Dropbox')
                    link = dBox.upload_file_with_link(ctx=ctx, file_from=files, file_to=file_to)
                    print(f'Created shared link {link}')
                    
                    embed = discord.Embed(
                        title=files,
                        url=link,
                        description=f'File has been converted to MP3\n\n[Download it here]({link})',
                        color=0x0066ff
                    )
                    await embedded_downloader.edit(embed=embed, delete_after=3600)

                    os.remove(files)
                    print('File was deleted')
                # Send as attachment to channel
                else:
                    print('The file size is under 8MB')
                    bot.dispatch('upload_start', ctx, files)
                    embed = discord.Embed(
                        title=files,
                        url=new_url,
                        description=f'File has been converted to MP3 and embedded',
                        color=0x0066ff
                    )
                    await embedded_downloader.add_files(discord.File(files))
                    await embedded_downloader.edit(embed=embed, delete_after=3600)
                    print('File was sent')
                    bot.dispatch('upload_end', ctx, 'Embedded')

                    os.remove(files)
                    print('File was deleted')
        else:
            embed = discord.Embed(
                title='Error: General error',
                description='Something went wrong check out examples in !help.',
                color=0x0066ff
            )
            await ctx.channel.send(embed=embed, delete_after=30)
    else:
        print('Nothing to search for. Searchword is required.')

@bot.command()
async def info(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    embed = discord.Embed(
        title='Bot information',
        description='Github: [DJ-Helper](https://github.com/BeeLazy/DJ-Helper) v0.2.0\n\nCreated by <@516598387773014029> - Powered by [Lavalink](https://github.com/freyacodes/Lavalink), [Wavelink](https://github.com/PythonistaGuild/Wavelink), [youtube-dl](https://github.com/ytdl-org/youtube-dl)',
        color=0x0066ff
    )
    await ctx.send(embed=embed, delete_after=60)

@bot.command()
async def pause(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if vc.is_playing() and not vc.is_paused():
            print(f'Pausing track {vc.source.title}')
            # Update embedded player
            ep = bot.embedded_players.get(ctx.guild.id)
            embeddedPlayerChannel = bot.get_channel(ep[0])
            embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
            embed = discord.Embed(
                title=vc.source.title,
                url=vc.source.uri,
                description=f'<@{ctx.author.id}> paused {vc.source.title}({vc.track.duration}s) at ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position)*1000)) + f".\nOriginally requested by <@{vc.source.info.get('QueuerId')}> in <#{vc.source.info.get('QueuerChannelId')}>"
            )
            embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
            await embeddedPlayer.edit(embed=embed)

            await vc.pause()
        else:
            await ctx.send('Nothing is playing.', delete_after=30)
    else:
        await ctx.send('The bot is not connected to a voice channel.', delete_after=30)

@bot.command()
async def play(ctx, *, search: wavelink.YouTubeTrack):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if not vc:
        custom_player = CustomPlayer()
        vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)

    if vc.is_playing() and not vc.is_paused():
        search.info.update({'EmbeddedPlayerChannelId': vc.track.info.get('EmbeddedPlayerChannelId'), 'EmbeddedPlayerId': vc.track.info.get('EmbeddedPlayerId'), 'QueuerId': ctx.author.id, 'QueuerChannelId': ctx.channel.id})
        vc.queue.put(item=search)

        embed = discord.Embed(
            title=search.title,
            url=search.uri,
            description=f'<@{ctx.author.id}> queued {search.title}'
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed, delete_after=30)
    else:
        # Check that bot is in same voice channel as queuer
        if not ctx.author.voice.channel.id == vc.channel.id:
            print(f'Queuer is currently in voicechannel {ctx.author.voice.channel.name}')
            print(f'Bot is currently in voicechannel {vc.channel.name}')
            print(f'Moving bot from {vc.channel.name}(id:{vc.channel.id}) to {ctx.author.voice.channel.name}(id:{ctx.author.voice.channel.id})')
            await vc.move_to(bot.get_channel(ctx.author.voice.channel.id))
            # Without sleep, the next calls to play will pass old data in the ctx object
            while vc.channel.id != ctx.author.voice.channel.id:
                await asyncio.sleep(0.1)

        # Update track metadata
        if not vc.track:
            search.info.update({'EmbeddedPlayerChannelId': ctx.channel.id, 'EmbeddedPlayerId': search.info.get('EmbeddedPlayerId'), 'QueuerId': ctx.author.id, 'QueuerChannelId': ctx.channel.id})
            await vc.play(search)
        else: # User issuing play while player is paused
            # One userfriendly feature would be to clear the current playing track, or entire queue,
            # and put the users track in front of the queue, and play it
            # That would however lead to misuse like issuing pause then play to wipe others queueitems
            # so then one would need to implement command throttling and checks
            print(f'Queuing {search.title} and resuming playback of {vc.source.title}')
            vc.queue.put(item=search)
            # Update embedded player
            ep = bot.embedded_players.get(ctx.guild.id)
            embeddedPlayerChannel = bot.get_channel(ep[0])
            embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
            embed = discord.Embed(
                title=vc.source.title,
                url=vc.source.uri,
                description=f"<@{ctx.author.id}> queued [{search.title}]({search.uri})\nAnd resumed playback of {vc.source.title}({vc.track.duration}s)\nOriginally queued by <@{vc.source.info.get('QueuerId')}> in <#{vc.source.info.get('QueuerChannelId')}>"
            )
            embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
            await embeddedPlayer.edit(embed=embed)

            await vc.resume()

@bot.command()
async def playing(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if not vc.is_playing():
            return await ctx.send('Nothing is playing.')

        print(f'Current playing song info requested:{vc.source.title}({vc.source.uri})')
        embed = discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f'Currently playing {vc.source.title}({vc.track.duration}s) at ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position)*1000)) + f".\nOriginally requested by <@{vc.source.info.get('QueuerId')}> in <#{vc.source.info.get('QueuerChannelId')}>"
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed, delete_after=30)
        
        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.', delete_after=30)

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
            await ctx.send(embed=embed, delete_after=30)
        else:
            print('New position requested: [{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000)))
            embed = discord.Embed(
                title=vc.source.title,
                url=vc.source.uri,
                description=f'<@{ctx.author.id}> changed playback position of {vc.source.title} to ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000))
            )
            embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed, delete_after=30)
            await vc.seek((vc.position + position) * 1000)

        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.', delete_after=30)

@bot.command()
async def seek(ctx, *, position: int=0):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if not vc.is_playing():
            return await ctx.send('Nothing is playing.', delete_after=30)

        print('New position requested: [{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000)))
        embed = discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f'<@{ctx.author.id}> changed playback position of {vc.source.title} to ' + '[{0[0]:.0f}h {0[1]:.0f}m {0[2]:.0f}s]'.format(await timeTuple((vc.position + position)*1000))
        )
        embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed, delete_after=30)
        await vc.seek((vc.position + position) * 1000)
        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.', delete_after=30)

@bot.command()
async def skip(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if not vc.is_playing():
            return await ctx.send('Nothing is playing.', delete_after=30)
        if vc.queue.is_empty:
            return await vc.stop()

        await vc.seek(vc.track.length * 1000)
        if vc.is_paused():
            await vc.resume()
    else:
        await ctx.send('The bot is not connected to a voice channel.', delete_after=30)

@bot.command()
async def resume(ctx):
    print(f'Deleting user message {ctx.message.id}. Reason: Processed command')
    await ctx.message.delete()

    vc = ctx.voice_client
    if vc:
        if vc.is_paused():
            print(f'Pausing track {vc.source.title}')
            # Update embedded player
            ep = bot.embedded_players.get(ctx.guild.id)
            embeddedPlayerChannel = bot.get_channel(ep[0])
            embeddedPlayer = await embeddedPlayerChannel.fetch_message(ep[1])
            embed = discord.Embed(
                title=vc.source.title,
                url=vc.source.uri,
                description=f"<@{ctx.author.id}> resumed playback of {vc.source.title}({vc.track.duration}s)\nOriginally queued by <@{vc.source.info.get('QueuerId')}> in <#{vc.source.info.get('QueuerChannelId')}>"
            )
            embed.set_author(name=ctx.author.display_name, url=f'https://discordapp.com/users/{ctx.author.id}', icon_url=ctx.author.display_avatar)
            await embeddedPlayer.edit(embed=embed)

            await vc.resume()
        else:
            await ctx.send('Nothing is paused.', delete_after=30)
    else:
        await ctx.send('The bot is not connected to a voice channel', delete_after=30)

# Error handling
@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Could not find a track.', delete_after=30)
    else:
        await ctx.send('General error. Check that you are connected to a voice channel.', delete_after=30)

# Execution
bot.run(TOKEN)
