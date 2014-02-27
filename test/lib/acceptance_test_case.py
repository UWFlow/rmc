import os
import subprocess

from selenium import webdriver
import selenium.webdriver.chrome.service as service
import nose.plugins.attrib

import fixtures
import model_test_case
import test_server


@nose.plugins.attrib.attr('slow')
class AcceptanceTestCase(model_test_case.ModelTestCase):
    @classmethod
    def setUpClass(cls):
        model_test_case.ModelTestCase.setUpClass()

        chromedriver_path = subprocess.check_output(['which', 'chromedriver'])
        chromedriver_path = chromedriver_path.strip()

        AcceptanceTestCase.chromedriver_service = service.Service(
            executable_path=chromedriver_path,
            service_args=['--silent'],
            log_path=os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  'logs', 'chromedriver.log'))
        AcceptanceTestCase.chromedriver_service.start()

        test_server.start_server()

    def setUp(self):
        super(AcceptanceTestCase, self).setUp()

        fixtures.reset_db_with_fixtures()

        self.driver = webdriver.Remote(
            AcceptanceTestCase.chromedriver_service.service_url, {})

    def tearDown(self):
        super(AcceptanceTestCase, self).tearDown()
        self.driver.quit()

    @classmethod
    def tearDownClass(cls):
        model_test_case.ModelTestCase.tearDownClass()
        test_server.kill_server()
        AcceptanceTestCase.chromedriver_service.stop()
