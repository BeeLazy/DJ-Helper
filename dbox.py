import dropbox
from dropbox.sharing import SharedLinkSettings, RequestedVisibility

class DBox:
    """
    Usage:
    from dbox import DBox

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

    def upload_file(self, file_from, file_to):
        """
        Upload a file to Dropbox
        150MB max size
        Note: 350GB max with files_upload_session_start
        """
        self.bot.dispatch("upload_start", ctx, file_from)
        dbx = dropbox.Dropbox(self.access_token)
        with open(file_from, 'rb') as f:
            dbx.files_upload(f.read(), file_to)

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
