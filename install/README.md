# API Install Instructions

This short guide will walk you through setting up the API locally. Most people won't need to do this as you can use the API remotely without having it installed locally. However, if you want to contribute to the API's code, you'll need to get it running locally.

First, message one of the admins for a copy of the test postgres database (wagetheft_postgres_database).

Then, create the database:

```sudo -u postgres createdb wagetheft```

Load the data:

```sudo -u postgres pg_restore -d wagetheft wagetheft_postgres_database```

Create a read only user for use by the api:

```
sudo -u posgres psql -d wagetheft

CREATE USER web WITH PASSWORD 'INSERT PASSWORD HERE';

GRANT SELECT ON ALL TABLES IN SCHEMA public TO web;
```

Install pip, dev, and nginx:

```
sudo apt-get update
sudo apt-get install python3-pip python3-dev nginx
```

Use pip to set the virtual env:

```sudo pip3 install virtualenv```


Clone the wagetheft API files to /var/www/api:

```
cd /var/www/
sudo git clone https://github.com/wagetheft/api
```


Setup the API's Python virtual environment:

```
sudo mkdir /var/www/.virtualenvs
cd /var/www/.virtualenvs
sudo virtualenv -p python3 wagetheftapi
source /var/www/.virtualenvs/wagetheftapi/bin/activate
```


Install required python modules:

```sudo pip install -r /var/www/api/requirements.txt```


Install uswgi

```sudo pip install uwsgi```

Create a folder called .sockets in /var/www and change the permissions to 755. Then change user and group owner of the folder to www-data:

```
sudo mkdir /var/www/.sockets
sudo chmod 755 /var/www/.sockets
sudo chown www-data:www-data /var/www/.sockets
```


Copy the config-templates into your api folder:

```sudo cp /var/www/api/install/config-templates/* /var/www/api```


If you are using a folder other than /var/www/api or selected a different location for the .sockets folder,  then you will need to change the settings in uwsgi.ini, wagetheftapi.service, and nginx-wagetheftapi.conf to reflect the correct location of your files and the sockets folder:

```
sudo nano uwsgi.ini
sudo nano wagetheftapi.service
sudo nano nginx-wagetheftapi.conf
```

If you are using /var/www/api and /var/www/.sockets as recommended, then no need to look at the settings at all.

Move the wagetheftapi.service file to the etc/systemd/system folder:

```sudo mv /var/www/api/uwsgi-wagetheftapi.service /etc/systemd/system```


Start the uwsgi service and enable it to run on startup:

```
sudo systemctl start uwsgi-wagetheftapi
sudo systemctl enable uwsgi-wagetheftapi
```


Create a symlink to the file for easy editing later:

```sudo ln -s /etc/systemd/system/uwsgi-wagetheftapi.service uwsgi-wagetheftapi.service```


Check that the service is running by seeing if the /var/www/.sockets/wagetheftapi.socket file exists:

```ls -l /var/www/.sockets```


Other commands you may need in the future:

```
sudo systemctl stop uwsgi-wagetheft
sudo systemctl restart uwsgi-wagetheft
```


Edit the nginx-wagetheftapi.conf file to reflect the url of the server or to run on a different port:

```sudo nano /var/www/api/nginx-wagetheftapi.conf```

Create a link to the nginx config file in /etc/nginx/sites-available and /etc/nginx/sites-enabled:

```
sudo ln -s /var/www/api/nginx-wagetheftapi.conf /etc/nginx/sites-available
sudo ln -s /var/www/api/nginx-wagetheftapi.conf /etc/nginx/sites-enabled
```


Restart nginx:

```sudo systemctl restart nginx```


Deactivate the virtual environment:

```deactivate```

