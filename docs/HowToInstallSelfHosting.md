# How to install self hosting
This document describes how to add self hosting as an option to embedding files and using other hosting solutions like Dropbox

## Description
To do selfhosting, we will install nginx on the same server as the discord bot is running. We will also install short_url to make neat short urls for us.

## Installation
Update ubuntu, and install nginx
```code
sudo apt-get update
sudo apt-get install nginx
```

Configure the firewall
```code
sudo ufw app list
sudo ufw allow 'Nginx Full'
sudo ufw status
```

Test nginx, and some usefull commands
```code
systemctl status nginx
http://127.0.0.1
sudo systemctl start nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo systemctl disable nginx
sudo systemctl enable nginx
```

Nginx on Ubuntu 22.04 has one server block enabled by default that is configured to serve documents out of a directory at /var/www/html. Instead of modifying /var/www/html, let’s create a directory structure within /var/www for our hosting site, leaving /var/www/html in place as the default directory to be served if a client request doesn’t match any other sites. Let's say our domain is mydomain.com, and I want to call the site media
```code
sudo mkdir -p /var/www/media.mydomain.com
sudo chown -R $USER:$USER /var/www/media.mydomain.com
sudo chmod -R 755 /var/www/media.mydomain.com
nano /var/www/media.mydomain.com/index.html
```

Inside index.html, add the following sample HTML:
```code
<html>
    <head>
        <title>Welcome to media.mydomain.com</title>
    </head>
    <body>
        <h1>Enjoy your stay!</h1>
    </body>
</html>
```

In order for Nginx to serve this content, it’s necessary to create a server block with the correct directives. Instead of modifying the default configuration file directly, we'll make a new one at /etc/nginx/sites-available/media.mydomain.com:
```code
sudo nano /etc/nginx/sites-available/media.mydomain.com
```

Paste in the following configuration block, which is similar to the default, but updated for our new directory and domain name:
```code
server {
        listen 80;
        listen [::]:80;

        root /var/www/media.mydomain.com;
        index index.html;

        server_name media.mydomain.com;

        location / {
                try_files $uri $uri/ =404;
        }
}
```

Next, let’s enable the file by creating a link from it to the sites-enabled directory, which Nginx reads from during startup:

Note: Nginx uses a common practice called symbolic links, or symlinks, to track which of your server blocks are enabled. Creating a symlink is like creating a shortcut on disk, so that you could later delete the shortcut from the sites-enabled directory while keeping the server block in sites-available if you wanted to enable it.
```code
sudo ln -s /etc/nginx/sites-available/media.mydomain.com /etc/nginx/sites-enabled/
```

Two server blocks are now enabled and configured to respond to requests based on their listen and server_name directives:

- media.mydomain.com: Will respond to requests for media.mydomain.com.
- default: Will respond to any requests on port 80 that do not match the other two blocks.

Disable the default NGINX configuration file.
```code
sudo unlink /etc/nginx/sites-enabled/default
```

To avoid a possible hash bucket memory problem that can arise from adding additional server names, it is necessary to adjust a single value in the /etc/nginx/nginx.conf file. Open the file:
```code
sudo nano /etc/nginx/nginx.conf
```

Find the server_names_hash_bucket_size directive and remove the # symbol to uncomment the line.
```code
...
http {
    ...
    server_names_hash_bucket_size 64;
    ...
}
...
```

Test the config, then restart nginx to enable the changes:
```code
sudo nginx -t
sudo systemctl restart nginx
```

Add dns records for media.mydomain.com. Nginx should now be serving media.mydomain.com. You can test this by navigating to http://media.mydomain.com

### Setup HTTPS

Install certbot
```code
sudo snap install core
sudo snap refresh core
sudo apt-get remove certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

Run this command to get a certificate and have Certbot edit your nginx configuration automatically to serve it, turning on HTTPS access in a single step.
```code
sudo certbot --nginx
```

If you're feeling more conservative and would like to make the changes to your nginx configuration by hand, run this command.
```code
sudo certbot certonly --nginx
```

The Certbot packages on your system come with a cron job or systemd timer that will renew your certificates automatically before they expire. You will not need to run Certbot again, unless you change your configuration. You can test automatic renewal for your certificates by running this command:
```code
sudo certbot renew --dry-run
```

### Short url service

Let's add a service to make short url's just like tinyurl.

Since we're installing everything on one server in this guide, all we need to do is to add a script to generate the shortlink and redirect include files. And then edit the nginx configuration file to include the config files (it should be added as part of server block. Certbot have added some things in here too, but dont be confused, just get it in there). We'll put them in a subfolder to keep it tidy.
```code
server {
        listen 80;
        listen [::]:80;

        # include shorturl configuration files
        include shorturl/*.conf;

        root /var/www/media.mydomain.com;
        index index.html;

        server_name media.mydomain.com;

        location / {
                try_files $uri $uri/ =404;
        }
}
```

Allow mediafiles (on the server/site being redirected to. In this doc its the same server and site)
```code
server {
        listen 80;
        listen [::]:80;

        # include shorturl configuration files
        include shorturl/*.conf;

        root /var/www/media.mydomain.com;
        index index.html;

        server_name media.mydomain.com;

        location ~ "\.(mp3|mp4)$" {
                allow all; # allow mp3, mp4 etc
        }

        location / {
                try_files $uri $uri/ =404;
        }
}
```

Save the nginx configuration file, and rereload nginx config:
```code
sudo systemctl restart nginx
```

Install short_url, so we can make short url's
```code
pip3 install -U short_url
```

We will use sqlite to generate unique integers for us. That is natively supported in python, but we need the os tools, the databasefile and a couple of tables. Sqlite automatically creates the dbfile if it does not exist, so we only need to create the tables:
```code
sudo apt-get install sqlite
sudo nano ~/dj-helper/create_database.py
```

Insert into the create_database.py file:
```code
import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def main():
    database = "djhelper.db"

    sql_create_paths_table ="""CREATE TABLE IF NOT EXISTS paths (
                                    id integer PRIMARY KEY,
                                    lopathngurl text NOT NULL
                                ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        create_table(conn, sql_create_paths_table)
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
```

There is an empty djhelper.db included with the project, so there is normally no need to run the [code above](../create_database.py). 

The system should now be ready to do selfhosting.

### File locations

- /etc/nginx: The Nginx configuration directory. All of the Nginx configuration files reside here.
- /etc/nginx/nginx.conf: The main Nginx configuration file. This can be modified to make changes to the Nginx global configuration.
- /etc/nginx/sites-available/: The directory where per-site server blocks can be stored. Nginx will not use the configuration files found in this directory unless they are linked to the sites-enabled directory. Typically, all server block configuration is done in this directory, and then enabled by linking to the other directory.
- /etc/nginx/sites-enabled/: The directory where enabled per-site server blocks are stored. Typically, these are created by linking to configuration files found in the sites-available directory.
- /etc/nginx/snippets: This directory contains configuration fragments that can be included elsewhere in the Nginx configuration. Potentially repeatable configuration segments are good candidates for refactoring into snippets.

### Logs

- /var/log/nginx/access.log: Every request to your web server is recorded in this log file unless Nginx is configured to do otherwise.
- /var/log/nginx/error.log: Any Nginx errors will be recorded in this log.
