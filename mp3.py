import youtube_dl
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
