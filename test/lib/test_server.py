import atexit
import logging
import os
import requests
import signal
import subprocess
import time

import mongoengine as me

import rmc.server.server as server
import rmc.shared.constants as c

import fixtures

_server_proc = None

PORT = 5001


def start_server():
    global _server_proc
    if _server_proc is not None:
        return

    # For explanation of why os.setsid is necessary here, see
    # http://stackoverflow.com/q/4789837/303911
    env = {'PYTHONPATH': '..'}
    env.update(os.environ)
    _server_proc = subprocess.Popen(
        ['/usr/bin/env', 'python', __file__],
        env=env,
        preexec_fn=os.setsid
    )
    atexit.register(kill_server)

    # Wait for the server to finish booting
    while True:
        try:
            resp = requests.get("http://localhost:%d/" % PORT)
            if resp.ok:
                break
        except requests.ConnectionError:
            pass
        time.sleep(0.5)


def kill_server():
    global _server_proc
    if _server_proc is None:
        return
    os.killpg(_server_proc.pid, signal.SIGTERM)
    _server_proc = None

if __name__ == '__main__':
    me.connection.disconnect()
    me.connect(
        fixtures.DB_NAME,
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

    server.app.run(port=PORT)
