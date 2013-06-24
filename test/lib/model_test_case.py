import unittest

import mongoengine as me

import rmc.shared.constants as c

TEST_MONGO_DB_RMC = c.MONGO_DB_RMC + '_test'

class ModelTestCase(unittest.TestCase):
    @classmethod
    def connect_to_test_db(cls):
        me.connection.disconnect()
        me.connect(
            TEST_MONGO_DB_RMC,
            host=c.MONGO_HOST,
            port=c.MONGO_PORT
        )

    @classmethod
    def setUpClass(cls):
        cls.connect_to_test_db()

    @classmethod
    def drop_test_database(cls):
        connection = me.connection.get_connection()
        connection.drop_database(TEST_MONGO_DB_RMC)

    def setUp(self):
        ModelTestCase.drop_test_database()

    @classmethod
    def tearDownClass(cls):
        me.connection.disconnect()
        ModelTestCase.drop_test_database()

