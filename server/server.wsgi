import mongoengine as me

import rmc.shared.constants as c
from rmc.server.server import app

me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
