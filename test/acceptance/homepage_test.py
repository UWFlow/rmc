import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import rmc.test.lib as testlib

class HomepageTest(testlib.AcceptanceTestCase):
    def _css(self, selector):
        return self.driver.find_element_by_css_selector(selector)

    def _assert_has_link_to(self, href):
        links = self.driver.find_elements_by_css_selector('[href="%s"]' % href)
        self.assertTrue(any([l.is_displayed() for l in links]))

    def _assert_visible(self, element):
        self.assertTrue(element.is_displayed())

    def test_homepage_login(self):
        self.driver.get('http://localhost:5001/')

        self._assert_has_link_to('/courses')
        self._assert_has_link_to('/profile/demo')
        self._assert_has_link_to('/about')
        self._assert_has_link_to('https://twitter.com/useflow')
        self._assert_has_link_to('http://facebook.com/planyourflow')

        fb_login_button = self._css('.fb-login-button')

        self._assert_visible(fb_login_button)

        time.sleep(0.1)

        fb_login_button.click()

        def window_opened(driver):
            return len(driver.window_handles) == 2

        wait = WebDriverWait(self.driver, 2)
        wait.until(window_opened)

        self.driver.switch_to_window(self.driver.window_handles[1])

        email_input = self.driver.find_element_by_name('email')
        pass_input = self.driver.find_element_by_name('pass')

        email_input.send_keys('wccnjoi_chengsen_1371789476@tfbnw.net')
        pass_input.send_keys('flowtestpass')
        pass_input.submit()

        self.driver.switch_to_window(self.driver.window_handles[0])

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.title_contains('Welcome'))
