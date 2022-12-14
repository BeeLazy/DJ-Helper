# DJ-Helper
This document describes how to install DJ-Helper.

## Installation

### Install on Ubuntu
DJ-Helper is written in python. If your installation don't have python3, you will need to install it.

First make a directory for the bot, and download the sourcecode into it.
```code
mkdir ~/dj-player
cd ~/dj-player
git clone https://github.com/BeeLazy/DJ-Helper.git .
```

The bot uses [Wavelink](https://github.com/PythonistaGuild/Wavelink) as a frontend to [Lavalink](https://github.com/freyacodes/Lavalink). So we need a Lavalink server. We could run their [Docker image](https://hub.docker.com/r/fredboat/lavalink/), but we will just run it with java on the same server as the bot.

It is recommended to use Oracle Java 13, but since it seems to run fine on Ubuntu 22.04 with openjdk 18, and we like open... we will install that:
```code
sudo apt-get install openjdk-18-jre-headless
```

Install wavelink, [discord.py](https://github.com/Rapptz/discord.py) and the other python libraries with pip:
```code
sudo apt-get install pip
pip3 install -U wavelink
pip3 install -U discord.py
pip3 install -U python-dotenv
pip3 install -U youtube_dl
pip3 install -U yt-dlp
pip3 install -U dropbox
```

Install [ffmpeg](https://github.com/FFmpeg/FFmpeg) to help with decoding and encoding:
```code
sudo apt-get install ffmpeg
```

Some of the settings are stored in environment variables. On Ubuntu one could f.ex store those in a .env file or in the global environment file. The following keys needs to be added:
- DISCORD_TOKEN
- LAVALINK_ADDRESS
- LAVALINK_PORT
- LAVALINK_PASSWORD
- DROPBOX_TOKEN
- DOWNLOAD_ENGINE
- HOSTING_PARENT
- HOSTING_REDIRECT_BASEURI
- HOSTING_BASEURI
- HOSTING_SMALL_FILES
- HOSTING_MEDIUM_FILES
- HOSTING_BIG_FILES
- HOSTING_ROOT

```code
sudo nano /etc/environment
source /etc/environment
echo $LAVALINK_PORT
```

Now we should have a working server. First we start Lavalink in a terminal:
```code
cd ~/dj-helper
java -jar Lavalink.jar
```

Hopefully Lavalink started up without problems, and we can run the bot in another terminal:
```code
cd ~/dj-helper
python3 bot.py
```

## Resources
[WaveLink documentation](https://wavelink.readthedocs.io/en/latest/)

[Lavalink documentation](https://lavalink.readthedocs.io/en/master/)

[discord.py documentation](https://discordpy.readthedocs.io/en/stable/)
