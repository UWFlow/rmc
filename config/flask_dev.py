import os

import rmc.shared.secrets as s

JS_DIR = 'js'
DEBUG = True
ENV = 'dev'
GA_PROPERTY_ID = 'UA-35073503-2'
LOG_DIR = os.path.join(os.getcwd(), 'logs')
FB_APP_ID = '289196947861602'
FB_APP_SECRET = s.FB_APP_SECRET_DEV
SECRET_KEY = s.FLASK_SECRET_KEY
