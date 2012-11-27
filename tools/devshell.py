#!/usr/bin/env python
"""Run an interactive shell in the rmc environment.

If IPython is installed, will use that as a REPL, otherwise will fall back to
regular python REPL.
"""

import os
import sys

import rootdir

sys.path.insert(0, os.path.dirname(rootdir.project_rootdir()))

try:
    import IPython

    try:
        # use default import
        from devshell_eval import *
    except Exception, e:
        print e

    # Useful imports
    IPython.embed()
except ImportError:
    print "=" * 78
    print "Looks like you don't have IPython installed."
    print "If you'd like to use IPython instead of the regular python REPL"
    print "pip install IPython"
    print "=" * 78
    import code
    code.interact(local=locals())
