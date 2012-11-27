import os
import sys

from rmc.config.flask_base import *
import rmc.shared.secrets as s

JS_DIR = 'js'
DEBUG = True
ENV = 'dev'
GA_PROPERTY_ID = 'UA-35073503-2'
LOG_DIR = os.path.join(sys.path[0], 'logs')
FB_APP_ID = '289196947861602'
FB_APP_SECRET = s.FB_APP_SECRET_DEV
