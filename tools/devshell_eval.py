# Useful things you want every time tools/devshell.py runs

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m
import rmc.shared.util as util
import rmc.shared.rmclogger as rmclogger

import mongoengine as me
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
