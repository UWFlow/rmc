import os
import subprocess
import signal
import time

from selenium import webdriver
import selenium.webdriver.chrome.service as service

import model_test_case


class AcceptanceTestCase(model_test_case.ModelTestCase):
    @classmethod
    def setUpClass(cls):
        model_test_case.ModelTestCase.setUpClass()

        chromedriver_path = subprocess.check_output(['which', 'chromedriver'])
        chromedriver_path = chromedriver_path.strip()

        AcceptanceTestCase.chromedriver_service = service.Service(
            executable_path=chromedriver_path,
            service_args=['--silent'],
            log_path=os.path.join(
                os.getcwd(), 'test', 'logs', 'chromedriver.log'
            )
        )
        AcceptanceTestCase.chromedriver_service.start()

        test_server_path = os.path.join(
            os.getcwd(), 'test', 'lib', 'test_server.py'
        )

        # For explanation of why os.setsid is necessary here, see
        # http://stackoverflow.com/q/4789837/303911
        AcceptanceTestCase.test_server_proc = subprocess.Popen(
            ['/usr/bin/python', test_server_path],
            env={'PYTHONPATH':'..'},
            preexec_fn=os.setsid
        )
        time.sleep(1)

    def setUp(self):
        super(AcceptanceTestCase, self).setUp()

        self.driver = webdriver.Remote(AcceptanceTestCase.chromedriver_service.service_url, {})

    def tearDown(self):
        super(AcceptanceTestCase, self).tearDown()
        self.driver.quit()

    @classmethod
    def tearDownClass(cls):
        model_test_case.ModelTestCase.tearDownClass()
        os.killpg(AcceptanceTestCase.test_server_proc.pid, signal.SIGTERM)
