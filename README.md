# Servers.tf #####

[Servers.tf](http://servers.tf/) (SVTF for short) is a browser-based server
browser for Source games such as Team Fortress 2 and Garry's Mod. The goal is
to be able to index servers so that far more sophisticated searches can be
made than what is currently possible with the current Source/Steam server
browser.

Ideally SVTF will be able to detect mods being ran by the server and be aware
of community-made game modes (e.g. Balloon Race or Surfing) so that the user
can perform richer searches to find more specific servers.


## Developing ####

The entire SVTF application is encapsulated by a single Python package:
`serverstf`. This package includes all the services needed to get a working
SVTF instance.


### Install `serverstf` ###

Python 3.4 is needed to run SVTF. It's advisable to install the package in
editable mode into an isolated environment, e.g. using `virtualenv`.

```shell
$ virtualenv -p $(which python3) env
$ . env/bin/activate
$ pip install -e .[development]
```

Note that `[development]` will ensure that development dependencies will
also be installed along side core packages. This includes things like
[Pylint](http://www.pylint.org/) which can be used to check the Python source.
Installing these extra packages isn't strictly necessary as long as you're
certain you won't need them -- e.g. you're just adding a map image.


### Install UI Dependencies ###

The SVTF user interface is primarily written using CoffeeScript and has
a number of external dependencies. These can be installed using `npm` and
`bower` with Grunt being used to manage compilation of scripts and
stylesheets.

```shell
$ npm install
$ node_modules/.bin/bower install
$ node_modules/.bin/grunt
```

It is advisable to use the `watch` Grunt task when actively working on
the user interface.


### Run the User Interface ###

The `serverstf` package includes a small [Pyramid](
https://github.com/Pylons/pyramid) application served via [Waitress](
https://github.com/Pylons/waitress) which runs the UI. As with all SVTF
services the UI server can be started by running the `serverstf` package
with a subcommand.

```
$ python -m serverstf ui 9000
$ xdg-open http://localhost:9000/
```
