[![Build Status](https://travis-ci.org/UWFlow/rmc.svg?branch=master)](https://travis-ci.org/UWFlow/rmc)

# Flow

Plan your courses

## Why RMC?

It might seem funny that this repository and much of the code references `rmc`.

RMC stands for "Rate My Courses", which was the prototype name for this project
before it was given the (slightly) better name of Flow.

Because of the profileration of this 3 letter prefix throughout the code, and the
unfortunate coupling of the repository name and our python namespace, we decided
to leave it be.

## Getting up and running

The fastest way to get started is to use Docker. This will let you run Flow 
inside of a virtual machine to avoid dealing with package installation problems, 
avoid polluting your development environment, and should take less 
time.

To get started, [install Docker][].

Once you have docker installed, run:

    $ make shell_in_docker

This will download and run a Docker image with all of Flow's dependencies 
already installed. Don't worry if you don't know what a Docker image is.

Flow will only need to download the image once, so booting up in the future should 
be much faster.

Once the Docker image is downloaded and running, you should find yourself in a
`/bin/bash` shell. This is running inside a Docker container (effectively a 
virtual machine). Inside this container, the `rmc` repository can be found in 
`/rmc`, which you should be in right after running `make shell_in_docker`.

To start running Flow locally, run the following inside this new shell.

    $ make local

If you point your browser at http://localhost:5000/, you should now see the Flow 
homepage running on your computer!

Congratulations! You now have Flow running locally.

[install Docker]: https://docs.docker.com/engine/installation/

## Getting seed data

To do anything interesting in Flow, you need data in your database. This is 
where information about courses, professors, and scheduling information is 
stored.

To get started, open a new terminal (different from the one running `make 
local`), and start a new shell inside Docker by running

    $ make shell_in_docker

Inside the Docker container, run the following to get some basic course data 
into the DB

    $ make init_data

## Directory structure


It may be helpful to read this document before diving into the code. This
isn't exhaustive, but it should be enough to get you started if you want to contribute.

- `config/`: Configuration for frameworks, databases, or anything that might vary between
            the development environment and production.
- `data/`: This is where we collect data and load it into the database
    - `crawler.py` downloads data by scraping pages and hitting APIs
    - `processor.py` processes the data grabbed by `crawler.py` and loads it into the DB
    - `aggregator.py` is run on a regular schedule (daily for the most part) to keep our data up to date
- `models/`: "Schema" definitions for our models backed by [MongoEngine][]
- `server/`: Request handlers, static assets, and templates
    - `templates/`: [Jinja2][] templates
        - Files in here ending with `_page.html` (e.g. `course_page.html`) are rendered directly by the
          [Flask][] server with `render_template` calls, with the exception of the `base_*_page.html`
          files which other `_page.html` templates inherit from.
        - Most of the other files (e.g. `course.html`) contain [Underscore templates][] used to render
          stuff on the client-side
    - `static`: Static assets eventually ending up as files served directly by [nginx][] when on production
        - `js`: All our JavaScript code, organized into [RequireJS][] modules
            - `ext/`: All third party JavaScript code
            - `main.js`: The entry point for JavaScript executing on page load
        - `sass`: We don't write CSS directly for Flow, we use the SCSS flavor of [Sass][], which compiles
                  down to CSS
    - `server.py`: The majority of the request handlers for the application, written in [Flask][]

[MongoEngine]: http://mongoengine.org/
[Jinja2]: http://jinja.pocoo.org/docs/
[Flask]: http://flask.pocoo.org/
[Underscore templates]: http://underscorejs.org/#template
[nginx]: http://wiki.nginx.org/Main
[RequireJS]: http://requirejs.org/
[Sass]: http://sass-lang.com/

## Using the REPL

If you need a REPL to fool around with the database or test out some code, check
out `tools/devshell.py`.

To automatically load some imports and connect to a database, setup code can be
found in `tools/devshell_eval.py`

Here's what an example session might look like:

    $ tools/devshell.py
    Python 2.7.1 (r271:86832, Jul 31 2011, 19:30:53)
    Type "copyright", "credits" or "license" for more information.

    IPython 0.13.1 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    In [1]: m.User.objects(first_name__in=['Jamie', 'David', 'Sandy', 'Mack'],
    last_name__in=['Wong', 'Hu', 'Duan', 'Wu'])
    Out[1]: [<User: David Hu>, <User: Mack Duan>, <User: Sandy Wu>, <User: Jamie Wong>]

[virtualenv]: http://www.virtualenv.org/en/latest/



## Running tests

To run all the tests in the entire system:

```
make alltest
```

To run all the tests except the really slow ones (namely [Selenium][] tests):

```
make test
```

To run all the tests under a specific directory tree or in a specific file:
```
PYTHONPATH=.. nosetests server/api
PYTHONPATH=.. nosetests server/api/v1_test.py
```

[Selenium]: http://docs.seleniumhq.org/projects/webdriver/

## Contributing

When you're ready to contribute, take a look at [the contributing
guidelines](https://github.com/UWFlow/rmc/blob/master/CONTRIBUTING.md) and our
[style guide](https://github.com/UWFlow/rmc/wiki/Flow-Style-Guide).

## Setting up without Docker

If you'd prefer to avoid the docker route, you can install the dependencies 
directly on your own machine.

To set up your dev environment, run `make install`.

We work inside a [virtualenv][], so remember to `source
~/.virtualenv/rmc/bin/activate` whenever you're working within the repo.

You should now be ready to boot the local server, with `make local`.

Once it starts running, point your browser to http://localhost:5000/

### MongoDB error on Linux

If you are getting a connection refused error when trying to run `make local` and are on Linux, it is
most likely due to MongoDB taking too long to start the first time it's run. To fix this, run `mongod --config config/mongodb_local.conf`
and let it warm up for about 30 seconds to 1 minute. Then end the process, and run `make local` again. It should work now.
