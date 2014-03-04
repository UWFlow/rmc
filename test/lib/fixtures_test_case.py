import fixtures
import model_test_case


class FixturesTestCase(model_test_case.ModelTestCase):

    @classmethod
    def setUpClass(cls):
        super(FixturesTestCase, cls).setUpClass()

        # NOTE: This is done on class setup instead of test setup because it's
        # very slow. This unfortunately means that any mutation of the database
        # within a test is persisted for the rest of the tests in each test
        # class.
        fixtures.reset_db_with_fixtures()

    @classmethod
    def tearDownClass(cls):
        super(FixturesTestCase, cls).tearDownClass()

    def setUp(self):
        # We intentionally don't call super here because ModelTestCase drops
        # the database on every test. We want to retain our fixtures to prevent
        # our tests from being very slow.
        pass
