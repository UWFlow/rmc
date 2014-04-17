import celery
import logging
import os
import subprocess

import rmc.shared.constants as c

app = celery.Celery('tasks', broker='redis://%(hostname)s:%(port)d/%(db)d' % {
    'hostname': c.REDIS_HOST,
    'port': c.REDIS_PORT,
    'db': c.REDIS_DB
})

app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ENABLE_UTC=True
)


@app.task
def render_schedule_screenshot(url_to_render, screenshot_filepath):
    with open(os.devnull, 'w') as devnull:
        logging.info('Rendering %s started', screenshot_filepath)

        retcode = subprocess.call(
            [
                "phantomjs",
                "--disk-cache=true",
                os.path.join(os.path.dirname(__file__),
                        "schedule_screenshot.js"),
                url_to_render,
                screenshot_filepath
            ],
            stderr=devnull,
            stdout=devnull
        )

        if retcode == 0:
            logging.info('Rendering %s successful', screenshot_filepath)
        elif retcode == 2:
            logging.error('Rendering %s timed out', screenshot_filepath)
        else:
            logging.error('Rendering %s failed (returned %d)',
                    screenshot_filepath, retcode)
