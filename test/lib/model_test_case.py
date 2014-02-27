import unittest

import mongoengine as me

import rmc.shared.constants as c
import fixtures


class ModelTestCase(unittest.TestCase):
    @classmethod
    def _connect_to_test_db(cls):
        me.connection.disconnect()
        me.connect(
            fixtures.DB_NAME,
            host=c.MONGO_HOST,
            port=c.MONGO_PORT
        )

    @classmethod
    def setUpClass(cls):
        cls._connect_to_test_db()

    @classmethod
    def _drop_test_database(cls):
        connection = me.connection.get_connection()
        connection.drop_database(fixtures.DB_NAME)

    def setUp(self):
        ModelTestCase._drop_test_database()

    @classmethod
    def tearDownClass(cls):
        me.connection.disconnect()
        ModelTestCase._drop_test_database()

