import rmc.test.lib as testlib

class HomepageTest(testlib.AcceptanceTestCase):
    def _css(self, selector):
        return self.driver.find_element_by_css_selector(selector)

    def _assert_has_link_to(self, href):
        links = self.driver.find_elements_by_css_selector('[href="%s"]' % href)
        self.assertTrue(any([l.is_displayed() for l in links]))

    def _assert_visible(self, element):
        self.assertTrue(element.is_displayed())

    def test_homepage_loads(self):
        self.driver.get('http://localhost:4321/')

        self._assert_has_link_to('/courses')
        self._assert_has_link_to('/profile/demo')
        self._assert_has_link_to('/about')
        self._assert_has_link_to('https://twitter.com/useflow')
        self._assert_has_link_to('http://facebook.com/planyourflow')

        fb_login_button = self._css('.fb-login-button')

        self._assert_visible(fb_login_button)
