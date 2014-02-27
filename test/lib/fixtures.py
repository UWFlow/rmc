import os
import subprocess


def reset_db_with_fixtures():
    """Overwrite the database with a seed database."""
    subprocess.check_output([
        'mongorestore', '--drop', os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'dump'
        )
    ])
