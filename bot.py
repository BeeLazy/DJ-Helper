import discord, youtube_dl, re, os, glob, mp3
import urllib.request
from os.path import getsize
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents()
intents.messages = True
intents.message_content = True
intents.reactions = False
intents.members = False
intents.guilds = False

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user} \n'.format(client))

    for guild in client.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # main command
    if message.content.startswith('/ytdl'):
        #get the message content
        msg = message.content
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
                    await message.channel.send(f'Downloading {url[0]}')
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

                            embedVar = discord.Embed(title="Something went wrong :confused:\n\nTry sending a song that is under 7 minutes long, \nbecause of Discord's file size limit.\n\nCheck out /help and /info commands.", color=0x0066ff)
                            await message.channel.send(embed=embedVar)

                            os.remove(files)
                            print('File was removed')
                        else:
                            await message.channel.send(file=discord.File(files))
                            print('File was sent...')

                            os.remove(files)
                            print('File was deleted...')
                else:
                    await message.channel.send(embed=embedVar)
                    print('The link was not valid')
            else:
                embedVar = discord.Embed(title="Something went wrong :confused: \n\nIt looks like you sent more than one url's, please send one url at time.\n\nCheck out /help and /info commands.", color=0x0066ff)
                await message.channel.send(embed=embedVar)
        elif not url:
            #split the message after the first space
            msg = msg.split(' ',1)
            print(msg[1])
            msg = msg[1].replace(' ','+')
            print(msg)

            # create a youtube search link with our string
            print(f'https://www.youtube.com/results?search_query={msg}')
            html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={msg}')
            video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())

            # construct a new url from the videos id's we got back
            new_url = 'https://www.youtube.com/watch?v=' + video_ids[0]
            print(new_url)

            await message.channel.send(f'Downloading {new_url}')
            await mp3.song([new_url])
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

                    embedVar = discord.Embed(title="Something went wrong :confused:\n\nTry sending a song that is under 7 minutes long, \nbecause of Discord's file size limit.\n\nCheck out /help and /info commands.", color=0x0066ff)
                    await message.channel.send(embed=embedVar)

                    os.remove(files)
                    print('File was deleted...')
                else:
                    #await message.channel.send(new_url)
                    await message.channel.send(file=discord.File(files))
                    print('File was sent...')

                    os.remove(files)
                    print('File was deleted...')
        else:
            embedVar = discord.Embed(title="Something went wrong check out examples in /help.", color=0x0066ff)
            await message.channel.send(embed=embedVar)

    # help command
    if message.content.startswith('/help'):
        embedVar = discord.Embed(title="List of commands with examples: \n /ytdl [youtube video link]\n /ytdl [song title]\n /help\n /info \n\n ** Important: The video length must be under 7 minutes long (8MB). **", color=0x0066ff)
        await message.channel.send(embed=embedVar)

    #info command
    if message.content.startswith('/info'):
        embedVar = discord.Embed(title="Bot information: \n\nGithub: [not public yet]\n\nCreated by Bee", color=0x0066ff)
        await message.channel.send(embed=embedVar)

client.run(TOKEN)
