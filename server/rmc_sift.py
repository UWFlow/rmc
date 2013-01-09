"""A wrapper around the Sift Science Python client to asynchronously send
events.
"""

from hotqueue import HotQueue

import rmc.server.sift_client as sift_client
import rmc.shared.constants as c


class RmcSift(object):
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = sift_client.Client(api_key=api_key)
        self.queue = HotQueue("sift_events", host=c.REDIS_HOST,
                port=c.REDIS_PORT, db=c.REDIS_DB)

    def track(self, event, params):
        self.queue.put({'event': event, 'params': params})

    def process_events(self):
        for item in self.queue.consume():
            self.client.track(item['event'], item['params'])


if __name__ == '__main__':
    rmc_sift = RmcSift(c.SIFT_API_KEY)
    rmc_sift.process_events()
