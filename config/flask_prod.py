import os

import rmc.shared.secrets as s

# TODO(david): Re-enable minification by changing this directory to 'js_prod'.
#     Minification was disabled in github.com/UWFlow/rmc/commit/52fae50b
#     to be able to debug Airbrake issues, but it looks like Airbrake supports
#     source maps now.
JS_DIR = 'js'

DEBUG = False
ENV = 'prod'
GA_PROPERTY_ID = 'UA-35073503-1'
LOG_DIR = '/home/rmc/logs'
LOG_PATH = os.path.join(LOG_DIR, 'server/server.log')
FB_APP_ID = '219309734863464'
FB_APP_SECRET = s.FB_APP_SECRET_PROD
SECRET_KEY = s.FLASK_SECRET_KEY
