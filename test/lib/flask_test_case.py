import json

import fixtures
import model_test_case
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


class FlaskTestCase(model_test_case.ModelTestCase):
    @classmethod
    def setUpClass(cls):
        model_test_case.ModelTestCase.setUpClass()
        # NOTE: This is done on class setup instead of test setup because it's
        # very slow. This unfortunately means that any mutation of the database
        # within a test is persisted for the rest of the tests in each test
        # class.
        fixtures.reset_db_with_fixtures()

    @classmethod
    def tearDownClass(cls):
        model_test_case.ModelTestCase.tearDownClass()

    def setUp(self):
        # We intentionally don't call super here because ModelTestCase drops
        # the database on every test. We want to retain our fixtures to prevent
        # our tests from being very slow.
        server.app.config.from_object('rmc.config.flask_test')
        self.app = server.app.test_client()
        self.maxDiff = None

    def assertResponseOk(self, resp):
        self.assertEquals(resp.status_code, 200)

    def assertJsonResponse(self, resp, expected):
        self.assertEqual(deunicode(json.loads(resp.data)), expected)

