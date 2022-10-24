import dropbox
from dropbox.sharing import SharedLinkSettings, RequestedVisibility
import shutil
from pathlib import Path
import short_url
import subprocess
import urllib.parse
from dotenv import load_dotenv
import os

# Environment
load_dotenv()
HOSTING_PARENT = os.getenv('HOSTING_PARENT')
HOSTING_REDIRECT_BASEURI = os.getenv('HOSTING_REDIRECT_BASEURI')
HOSTING_BASEURI = os.getenv('HOSTING_BASEURI')

class DBox:
    """
    Usage:
    from uploader import DBox

    access_token = '****'
	dBox = DBox(access_token)

	file_from = 'test.txt'
	file_to = '/some/path/test.txt'

	dBox.upload_file(file_from=file_from, file_to=file_to)
    dBox.create_shared_link(path=file_to)
    dBox.file_exists(file_to)
    dBox.file_is_shared(file_to)
    """
    
    def __init__(self, access_token, bot):
        self.access_token = access_token
        self.bot = bot

    def upload_file(self, ctx, file_from, file_to):
        """
        Upload a file to Dropbox
        150MB max size
        Note: 350GB max with files_upload_session_start
        """
        self.bot.dispatch("upload_start", ctx, file_from)
        dbx = dropbox.Dropbox(self.access_token)
        with open(file_from, 'rb') as f:
            dbx.files_upload(f.read(), file_to)
        print('File uploaded')
        self.bot.dispatch("upload_end", ctx, file_to)

    def upload_file_with_link(self, ctx, file_from, file_to):
        """
        Upload a file to Dropbox, returns shared_link
        150MB max size
        Note: 350GB max with files_upload_session_start
        """
        self.bot.dispatch("upload_start", ctx, file_from)
        dbx = dropbox.Dropbox(self.access_token)
        with open(file_from, 'rb') as f:
            dbx.files_upload(f.read(), file_to)
        
        shared_link = DBox.create_shared_link(self, path=file_to)

        self.bot.dispatch("upload_end", ctx, shared_link)
        return shared_link

    def file_exists(self, path):
        """
        Check if a file exists
        """
        dbx = dropbox.Dropbox(self.access_token)
        try:
            dbx.files_get_metadata(path)
            return True
        except:
            return False

    def file_is_shared(self, path):
        """
        Check if a file is shared
        """
        dbx = dropbox.Dropbox(self.access_token)
        try:
            res = dbx.sharing_list_shared_links(path=path, cursor=None, direct_only=True)
            res.links[0]
            return True
        except:
            return False

    def create_shared_link(self, path):
        """
        Create a shared link for a file in Dropbox

        Returns the shared link

        If the file is already shared, it returns the existing link
        """
        dbx = dropbox.Dropbox(self.access_token)
        if self.file_is_shared(path):
            res = dbx.sharing_list_shared_links(path=path, cursor=None, direct_only=True)
            return res.links[0].url
        else:
            link_settings = SharedLinkSettings(requested_visibility=RequestedVisibility.public)
            metadata = dbx.sharing_create_shared_link_with_settings(path, settings=link_settings)
            return metadata.url

class SHost:
    """
    Usage:
    from uploader import SHost

	sHost = SHost()

	file_from = 'test.txt'
	file_to = '/some/path/test.txt'

	sHost.upload_file(file_from=file_from, file_to=file_to)
    sHost.create_shared_link(path=file_to)
    sHost.file_exists(file_to)
    sHost.file_is_shared(file_to)
    """
    
    def __init__(self, database_connection, bot):
        self.database_connection = database_connection
        self.bot = bot
        self.host = HOSTING_REDIRECT_BASEURI
        self.media_host = HOSTING_BASEURI
        self.parent = HOSTING_PARENT

    def upload_file(self, ctx, file_from, file_to):
        """
        Upload a file to hosting
        No max size
        """
        self.bot.dispatch("upload_start", ctx, file_from)
        shutil.copy2(file_from, file_to)
        print('File uploaded')
        self.bot.dispatch("upload_end", ctx, file_to)

    def move_file(self, ctx, file_from, file_to):
        """
        Move a file
        No max size
        """
        self.bot.dispatch("upload_start", ctx, file_from)
        shutil.move(file_from, file_to)
        print('File uploaded')
        self.bot.dispatch("upload_end", ctx, file_to)

    def upload_file_with_link(self, ctx, file_from, file_to):
        """
        Upload a file to hosting, returns shared_link
        No max size
        """
        self.bot.dispatch("upload_start", ctx, file_from)
        shutil.copy2(file_from, file_to)
        print('File uploaded')
        
        shared_link = SHost.create_shared_link(self, path=file_from)

        self.bot.dispatch("upload_end", ctx, shared_link)
        return shared_link

    def file_exists(self, path):
        """
        Check if a file exists
        """
        if Path(path).is_file():
            return True
        else:
            return False

    def file_is_shared(self, path):
        """
        Check if a file is shared
        """
        cur = self.database_connection.cursor()
        cur.execute(f"SELECT id FROM paths WHERE path='{path}'")
        row = cur.fetchone()
        if row is None:
            return False
        else:
            return True

    def create_path(self, path):
        """
        Create a new path
        :return: id
        """
        print(f'Generating integer for path:{path}')

        sql ='''INSERT INTO paths(path)
                    VALUES(?) '''
        cur = self.database_connection.cursor()
        cur.execute(sql, [path])
        self.database_connection.commit()
        return cur.lastrowid

    def get_short_url(self, short):
        """
        Returns a full short url
        """
        short_url = f'{self.host}/{self.parent}/{short}'

        return short_url

    def get_shared_url(self, path):
        """
        Returns a full shared url
        """
        shared_url = f'{self.media_host}/{self.parent}/{urllib.parse.quote(path)}'

        return shared_url

    def create_shared_link(self, path): # file_from
        """
        Create a shared link for a hosted file

        Returns the shared link

        If the file is already shared, it returns the existing link
        """
        cur = self.database_connection.cursor()
        cur.execute(f"SELECT id FROM paths WHERE path='{path}'")
        row = cur.fetchone()
        if row is None:
            # generate short_url from id
            id = SHost.create_path(self, path=path)
            short = short_url.encode_url(id)
            shared_link = SHost.get_short_url(self, short=short)
            destination_link = SHost.get_shared_url(self, path=path)
            # Create redirect
            with open(f'/etc/nginx/shorturl/{short}.conf', 'w') as redirect_file:
                redirect_file.write('location = /{0}/{1} {{return 301 {2};}}'.format(self.parent, short, destination_link))
            # Reload nginx
            subprocess.call('sudo systemctl reload nginx', shell=True)

            return shared_link
        else:
            short = short_url.encode_url(row[0])
            shared_link = SHost.get_short_url(self, short=short)
            return shared_link
