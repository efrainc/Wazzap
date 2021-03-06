# Wazzap
Group Project - for Python developer project Code Fellows


Wazzap is built to help poeple find events to got to on a night out. It works by allowing a users to enter venues in the search box and when their venue is found, it will put a marker on the map for that venue. When they click that marker, they can now see the latest tweets from that venue. There is some amount of filtering for tweets that look life events. 


It uses an RDS Postgres database and an EC2 instance or it can be run locally by creating a local Postegres database. The database contains two tables, one for tweets and another for locations. When the user enters a new, venue, it adds that venue to the database and renders the marker on the map. When the user clicks on a marker, it will pull tweets from the location and put them into the tweets table. Every night at 12:00 midnight, we update the tweets.  

## Wazzap [procedures]

### Fab commands to use our app:

```Shell
$install_nginx_wazzap
```

Use to install nginx to our instance

```Shell
$deploy_wazzap
```

Upload everything in our project folder,  ~/projects/wazzap/ up to ~/wazzap on our instance

```Shell
$ssh_wazzap
```

Log onto our instance


### Instructions for deploying new dbase schema:
1. Log into our dbase:

```Shell
ubuntu@ip-172-31-21-125:~$ psql --host=wazzapdbinstance.cskx7uviv9zs.us-west-2.rds.amazonaws.com --port=5432 --username=wazzapuser --dbname=wazzapdbase
Password for user wazzapuser:wazzappaskey
```

2. Remove the dbase tables:


```Shell
wazzapdbase=> DROP TABLE tweets
wazzapdbase-> DROP TABLE locals
wazzapdbase-> \q
```

3. Go into python in the wazzap directory:


```Shell
ubuntu@ip-172-31-21-125:~$ cd wazzap
ubuntu@ip-172-31-21-125:~/wazzap$ python
```

4. Initialize and the database and populate the locations database:


```Shell
>>> import webapp
>>> webapp.init_db()
>>>webapp.setup_data_snapshot()
>>>exit()
```

### Restart Supervisor (Automatic Way):


```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ supervisorctl restart webapp
```

### Restart Supervisor (Manual Way):
1. show processes:


```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ ps -e
```

2. kill process:


```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ sudo kill <id of supervisord>
```

3. start supervisor


```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ supervisord
```

### To Restart nginx:

```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ sudo /etc/init.d/nginx restart
```

###Controlling the Auto Update:
###Show update schedule:

```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ crontab -l
```

### Editing the Update Schedule (With Care):


```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ export EDITORS = vi
ubuntu@ip-172-31-21-125:~/wazzap$ crontab -e
```
(displays in minutes first, then hours, then days)

### Deleting GeoJSON (Start Points):

```Shell
ubuntu@ip-172-31-21-125:~/wazzap$ python
>>> from write_json import delete_venues
>>> delete_venues()
>>>exit()
```


## Future Additions:
Allow login so each member has their own pins.
Allow deletion of pins

## Long term Future additions:
Increase pin (or graphic) size with number of attendees. 
Give additional details (example if its a concert/link to ticket site) 
Gather data from other sites - facebook..ects. 
Maybe built in with Uber or local transportation apps (one bus away) for travel considerations. 
Let me bookmark events for the future. Maybe sends me an email reminder of an event or a text message. 

## Resources used:
Tweepy API: http://www.tweepy.org/
Google Maps API: https://developers.google.com/maps/
