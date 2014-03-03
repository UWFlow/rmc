import json

import fixtures_test_case
import rmc.server.server as server


def deunicode(obj):
    """Convert all unicode strings in an API response to regular strings."""
    if isinstance(obj, basestring):
        return str(obj)
    if isinstance(obj, list):
        return [deunicode(v) for v in obj]
    if isinstance(obj, dict):
        return dict((str(k), deunicode(v)) for (k, v) in obj.iteritems())
    return obj


class FlaskTestCase(fixtures_test_case.FixturesTestCase):

    def setUp(self):
        super(FlaskTestCase, self).setUp()
        server.app.config.from_object('rmc.config.flask_test')
        self.app = server.app.test_client()
        self.maxDiff = None

    def assertResponseOk(self, resp):
        self.assertEquals(resp.status_code, 200)

    def assertJsonResponse(self, resp, expected):
        self.assertEqual(deunicode(json.loads(resp.data)), expected)

