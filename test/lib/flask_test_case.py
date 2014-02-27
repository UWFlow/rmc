import fixtures
import model_test_case

import rmc.server.server as server


class FlaskTestCase(model_test_case.ModelTestCase):
    @classmethod
    def setUpClass(cls):
        model_test_case.ModelTestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        model_test_case.ModelTestCase.tearDownClass()

    def setUp(self):
        super(FlaskTestCase, self).setUp()
        server.app.config.from_object('rmc.config.flask_test')
        fixtures.reset_db_with_fixtures()
        self.app = server.app.test_client()
        self.maxDiff = None
