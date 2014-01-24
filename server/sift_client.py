"""Python client for Sift Science's REST API
(https://siftscience.com/docs/rest-api).
"""

import json
import logging
import traceback

import requests


API_URL = 'https://api.siftscience.com/v202/events'
sift_logger = logging.getLogger('sift_client')


class Client(object):
    def __init__(self, api_key, api_url=API_URL, timeout=2.0):
        """Initialize the client.

        Args:
            api_key: Your Sift Science API key associated with your customer
                account. You can obtain this from
                https://siftscience.com/quickstart
            api_url: The URL to send events to.
            timeout: Number of seconds to wait before failing request. Defaults
                to 2 seconds.
        """
        self.api_key = api_key
        self.url = api_url
        self.timeout = timeout

    def track(self, event, properties):
        """Track an event and associated properties to the Sift Science client.
        This call is blocking.

        Args:
            event: The name of the event to send. This can either be a reserved
                event name such as "$transaction" or "$label" or a custom event
                name (that does not start with a $).
            properties: A dict of additional event-specific attributes to track
        Returns:
            A requests.Response object if the track call succeeded, otherwise
            a subclass of requests.exceptions.RequestException indicating the
            exception that occurred.
        """
        headers = { 'Content-type' : 'application/json', 'Accept' : '*/*' }
        properties.update({ '$api_key': self.api_key, '$type': event })

        try:
            response = requests.post(self.url, data=json.dumps(properties),
                    headers=headers, timeout=self.timeout)
            # TODO(david): Wrap the response object in a class
            return response
        except requests.exceptions.RequestException as e:
            sift_logger.warn('Failed to track event: %s' % properties)
            sift_logger.warn(traceback.format_exception_only(type(e), e))

            return e
