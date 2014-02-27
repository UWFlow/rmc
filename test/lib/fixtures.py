import os
import subprocess

# NOTE: This must match the directory name immediately inside of
# test/lib/fixtures
DB_NAME = "rmc_test"


def reset_db_with_fixtures():
    """Overwrite the database with a seed database."""
    with open(os.devnull) as devnull:
        subprocess.check_call([
            'mongorestore', '--drop', os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'dump'
            )
        ], stdout=devnull, stderr=devnull)
