import rmc.test.lib as testlib

class HomepageTest(testlib.AcceptanceTestCase):
    def test_homepage_loads(self):
        self.driver.get('http://localhost:4321/')
