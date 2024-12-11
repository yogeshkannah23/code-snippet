# FASTAPI PRODUCTION SETUP WITH NGINX & UVICORN
### Prerequisites
- Gunicorn
- Uvicorn
- Nginx &
Required packages for your project

_Note: Please make sure your project running correctly and 


## Testing Uvicorn’s to Serve the Project
We can test this by entering the project directory and using gunicorn to load the project’s WSGI module:
- `Gunicorn`
```
uvicorn app:app --host 0.0.0.0 --port 8000
```


## Creating systemd Socket and Service Files

Start by creating and opening a systemd socket file for Gunicorn with sudo privileges:
```
sudo nano /etc/systemd/system/gunicorn.socket
```

Inside, We will create a [Unit] section to describe the socket, a [Socket] section to define the socket location, and an [Install] section to make sure the socket is created at the right time:

### gunicorn.socket
File name `gunicorn.socket` 
```
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```
Save and close the file when you are finished

Next, Create and open a systemd service file for Gunicorn with sudo privileges in your text editor. The service filename should match the socket filename with exception of the extension
```
sudo nano /etc/systemd/system/gunicorn.service
```
### gunicorn.service
File name `gunicorn.service`

Note:
- Change the `WorkingDirectory` as well. and in the `ExecStart` change the `Virtual Environment` directory/
```
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=server1
Group=www-data
WorkingDirectory=/home/server1/code-snippet
ExecStart=/home/server1/code-snippet/venv/bin/gunicorn \
          --access-logfile - \
          --workers 5 \
          --bind unix:/run/gunicorn.sock \
          --worker-class uvicorn.workers.UvicornWorker \
          app:app

[Install]
WantedBy=multi-user.target
```

1. Start with the [Unit] section, which is used to specify metadata and dependencies.
   - Put a description of the service here and tell the init system to only start this after the networking target has been reached.
   - Because your service relies on the socket from the socket file, you need to include a Requires directive to indicate that relationship
2. Next, you’ll open up the [Service] section
   - Specify the user and group that you want to process to run under.
   - You will give your regular user account ownership of the process since it owns all of the relevant files. You’ll give group ownership to the www-data group so that Nginx can communicate easily with Gunicorn.
   - Then you’ll map out the working directory and specify the command to use to start the service.
   - In this case, you have to specify the full path to the Gunicorn executable, which is installed within our virtual environment.
   - You will then bind the process to the Unix socket you created within the /run directory so that the process can communicate with Nginx.
   - You log all data to standard output so that the journald process can collect the Gunicorn logs. You can also specify any optional Gunicorn tweaks here. For example, you specified 3 worker processes in this case:
3. Finally, We’ll add an [Install] section.
   - This will tell systemd what to link this service to if you enable it to start at boot. You want this service to start when the regular multi-user system is up and running

With that, your systemd service file is complete. Save and close it now.

You can now start and enable the Gunicorn socket. This will create the socket file at /run/gunicorn.sock now and at boot. When a connection is made to that socket, systemd will automatically start the gunicorn.service to handle it:
```
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```
You can confirm that the operation was successful by checking for the socket file.

## Checking for the Gunicorn socket file
Check the status of the process to find out whether it was able to start:
```
sudo systemctl status gunicorn.socket
```


Next, check for the existence of the gunicorn.sock file within the /run directory:
```
file /run/gunicorn.sock
```
```
Output
/run/gunicorn.sock: socket
```

## Testing Socket Activation
Currently, if you’ve only started the gunicorn.socket unit, the gunicorn.service will not be active yet since the socket has not yet received any connections. You can check this by typing:
```
sudo systemctl status gunicorn
```
You should receive output like this
```
Output
○ gunicorn.service - gunicorn daemon
     Loaded: loaded (/etc/systemd/system/gunicorn.service; disabled; vendor preset: enabled)
     Active: inactive (dead)
TriggeredBy: ● gunicorn.socket
```
You can verify that the Gunicorn service is running by typing:
```
sudo systemctl status gunicorn
```
 
## Configure Nginx to Proxy Pass to Gunicorn
Now that Gunicorn is set up, you need to configure Nginx to pass traffic to the process
Start by creating and opening a new server block in Nginx sites-available directory
```
sudo nano /etc/nginx/sites-available/code-snippet
```
Inside /etc/nginx/sites-available/code-snippet
```
server {
    listen 80;
    server_name m2m.softsuavetestandpocs.in;
    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```
- In server block We're specifying that this should listen on the normal port 80 and it should response to our server's domain or IP address
- Next Step, We'll tell Nginx to ignore any problems with finding a favicon. We'll also tell it where to find the static assets that we've collected in our projectdir/static directory. All of these files have a standand URI prefix of "/static", So we can create a location block to match those requests.
- Finally, Create a location / {} block to match all other requests. Inside of this location, We'll include the standard proxy_params(Forwarding to app server) file included with the Nginx installation and then pass the traffic directly to the gunicorn socket

Save and close the file when We're finished. Now we can enable the file by linking it to the sites-enabled directory
```
sudo ln -s /etc/nginx/sites-available/code-snippet /etc/nginx/sites-enabled
```

Test our Nginx configuration for syntax errors by typing
```
sudo nginx -t
```
If no errors are reported, go ahead and restart Nginx by typing:
```
sudo systemctl restart nginx
```


Finally, We will need to open up our firewall to normal traffic on port 80. Since we no longer need access to the development server, We can remove the rule to open port 8000 as well:
```
sudo ufw delete allow 8000
sudo ufw allow 'Nginx Full'
```

We should now be able to go to our server’s domain or IP address to view our application.