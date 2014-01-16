# Useful things you want every time tools/devshell.py runs

import rmc.shared.constants as c  # @UnusedImport
import rmc.shared.secrets as s  # @UnusedImport
import rmc.models as m  # @UnusedImport
import rmc.shared.util as util  # @UnusedImport
import rmc.shared.rmclogger as rmclogger  # @UnusedImport
import rmc.shared.facebook as f  # @UnusedImport

import mongoengine as me
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

from rmc.analytics.stats import *
