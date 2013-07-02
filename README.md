serverstf
=========

Web-based TF2 server browser written in Python using Django.

### Requirements

* Python 2.7
* Django 1.5
* [pysteam](http://github.com/Holiverh/pysteam)
* [python-openid](https://github.com/openid/python-openid)
* [MaxMind GeoLite City database](http://dev.maxmind.com/geoip/legacy/geolite)

    #### Database
    * Preferably MySQL or PostgreSQL; both untested so far but should avoid issues with concurrency that SQLite experiences.
    
    #### Migrations
    * [South](http://south.aeracode.org/) should preferably also be installed to handle migrations

### Installation
* Install Python
* Install Django
* Install South (optional)
* Clone repo/Extract archive
* **cd** into **serverstf/**
* Customise **settings-dist.py** as needed and rename to *settings.py*:
    * Switch to MySQL/PostgreSQL if available
    * A Steam API key can be acquired from
http://steamcommunity.com/dev/registerkey
* **python manage.py syncdb**
* **python manage.py syncmaster all**
    * You might need to specify the --address argument for syncmaster which can be found in %PROGRAMFILES%/Steam/config/MasterServers2.vdf under "hl2"
    * *Warning:* Very long running process; can take hours to complete although it's perfectly safe to exit at any time.
* **python manage.py activityd --nthreads=16**
    * A lot of waiting on IO resources so performance scales well with addtional threads
    * If using SQLite it's not reccomended to have this running whilst the server is.
* **python manage.py runserver**
* start http://localhost:8000/

### Usage
The listing for any region can be found in hte header at the top. However going straight to an unfiltered region set currently is **highly unreccomended** due to perfromance issues.

To filter and sort server lists you can enter tags within hte search bar at hthe bottom of a list or add them to the end of the list URL.

A very simple tag syntax is used: tags starting with a **+** are set to be *required* meaning any servers without that tag are filtered out. Those starting with a **-** are *igorned* causing any matching servers to be exlcuded from the list. Those without any prefix are considered *preferd*, so that the servers with the most matching prefered tags are sotred to the top.

#### Current tag list
* full
* active
* bots
* trade
* vsh
* mge
* jump
* surf
* alltalk
* teamtalk
* nocrit
* nospread
* nobulletspread
* soap
* rtd
* stats
* robot
* randomiser
* prophunt
* hunted
* ~~dodgeball~~
* quakesounds
* goomba
* password
* vac
* smac
