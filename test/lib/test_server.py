import logging
import os

import mongoengine as me

import rmc.server.server as server
import rmc.shared.constants as c

TEST_MONGO_DB_RMC = c.MONGO_DB_RMC + '_test'

if __name__ == '__main__':

    me.connection.disconnect()
    me.connect(
        TEST_MONGO_DB_RMC,
        host=c.MONGO_HOST,
        port=c.MONGO_PORT
    )

    server.app.config.from_object('rmc.config.flask_test')

    logging.basicConfig(
        level=logging.DEBUG,
        filename=os.path.join(
            server.app.config['LOG_DIR'], 'server.log'
        )
    )

    server.app.run(port=4321)
