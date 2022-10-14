import youtube_dl
import yt_dlp
import functools
import typing
import asyncio

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

class ytd:
    def __init__(self, bot):
        self.bot = bot
    
    @to_thread
    def song(self, ctx, url):
        self.bot.dispatch('download_start', ctx, url)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.mp3',
            'ignoreerrors': False,
            'nonplaylist': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        print('Song downloaded')
        self.bot.dispatch('download_end', ctx, url)

    @to_thread
    def mp4(self, ctx, url):
        self.bot.dispatch('download_start', ctx, url)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.mp4',
            'ignoreerrors': False,
            'nonplaylist': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        print('MP4 downloaded')
        self.bot.dispatch('download_end', ctx, url)

class ytdlp:
    def __init__(self, bot):
        self.bot = bot
    
    @to_thread
    def song(self, ctx, url):
        self.bot.dispatch('download_start', ctx, url)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title).200s_[%(id)s].%(ext)s',
            #'extract_audio' : True,
            #'audio_format' : 'mp3',
            #'audio_quality' : 0,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'ignoreerrors': False,
            'nonplaylist': True,
            'restrictfilenames' : True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        print('Song downloaded')
        self.bot.dispatch('download_end', ctx, url)

    @to_thread
    def mp4(self, ctx, url):
        self.bot.dispatch('download_start', ctx, url)
        ydl_opts = {
            # Download the best mp4 video available, or the best video if no mp4 available
            'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b',
            'outtmpl': '%(title).200s_[%(id)s].%(ext)s',
            'ignoreerrors': False,
            'nonplaylist': True,
            'restrictfilenames' : True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        print('MP4 downloaded')
        self.bot.dispatch('download_end', ctx, url)
