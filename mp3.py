import youtube_dl, os, glob
import functools
import typing
import asyncio

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

@to_thread
def song(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.mp3',
        'ignoreerrors': False,
        'nonplaylist': True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)
    print('Video downloaded...')
