"""Finds the root of the project-tree where the tests are currently being run.

Basically, it finds the directory above this file that has requirements.txt in it.
"""

import os

def project_rootdir():
    rootdir = os.path.dirname(__file__)
    while True:  # do while loop
        if os.path.exists(os.path.join(rootdir, 'requirements.txt')):
            return os.path.abspath(rootdir)

        old_rootdir = rootdir
        rootdir = os.path.dirname(rootdir)

        if rootdir == old_rootdir:
            # we're at and haven't found requirements.txt
            raise IOError('Unable to find requirements.txt above cwd: %s'
                          % os.path.dirname(__file__))
