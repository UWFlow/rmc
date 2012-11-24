import os

from rmc.config.flask_base import *

JS_DIR = 'js_prod'
DEBUG = False
ENV = 'prod'
GA_PROPERTY_ID = 'UA-35073503-1'
LOG_DIR = '/home/rmc/logs'
LOG_PATH = os.path.join(LOG_DIR, 'server/server.log')
