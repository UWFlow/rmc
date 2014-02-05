# Flow

Plan your courses

## Getting up and running

To set up your dev environment, run `make install`.

We work inside a [virtualenv][], so remember to `source
~/.virtualenv/rmc/bin/activate` whenever you're working within the repo.

You should now be ready to boot the local server, with `make local`.

Once it starts running, point your browser to http://localhost:5000/

## Getting production data

Once your local server is running, ask a Flow admin for a data dump.

Then, run the following:

```sh
mongorestore --drop PATH_TO_DUMP
make aggregate_data
```

After this, your local database should be populated with the same data as prod.
The easiest way of checking this is probably just to log in and search. You
should see all your connections with friends.

## Using the REPL

If you need a REPL to fool around with the database or test out some code, check
out `tools/devshell.py`.

It automatically loads some imports and connects to the database for you. This
setup code can be found in `tools/devshell_eval.py`.

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

## Contributing

When you're ready to contribute, take a look at [the contributing
guidelines](https://github.com/divad12/rmc/blob/master/CONTRIBUTING.md) and our
[style guide](https://github.com/divad12/rmc/wiki/Flow-Style-Guide).
