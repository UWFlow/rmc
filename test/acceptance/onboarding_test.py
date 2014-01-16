import os
import time
import rmc.models as m

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import rmc.test.lib as testlib


def window_opened(driver):
    return len(driver.window_handles) == 2


class OnboardingTest(testlib.AcceptanceTestCase):
    def _css(self, selector):
        return self.driver.find_element_by_css_selector(selector)

    def _css_all(self, selector):
        return self.driver.find_elements_by_css_selector(selector)

    def _wait_for_element(self, selector, delay=10):
        wait = WebDriverWait(self.driver, delay)
        wait.until(lambda d: d.find_element_by_css_selector(selector))

    def _assert_has_link_to(self, href):
        links = self.driver.find_elements_by_css_selector('[href="%s"]' % href)
        self.assertTrue(any([l.is_displayed() for l in links]))

    def _assert_visible(self, element):
        self.assertTrue(element.is_displayed())

    def _assert_homepage_state(self):
        self._assert_has_link_to('/courses')
        self._assert_has_link_to('/profile/demo')
        self._assert_has_link_to('/about')
        self._assert_has_link_to('https://twitter.com/useflow')
        self._assert_has_link_to('http://facebook.com/planyourflow')

    def _login(self):
        fb_login_button = self._css('.fb-login-button')

        self._assert_visible(fb_login_button)

        time.sleep(0.1)

        fb_login_button.click()

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
        wait.until(lambda d: d.find_element_by_class_name("transcript-text"))

    def _paste_transcript(self):
        selector = ".transcript-text"
        textarea = self._css(selector)

        transcript_txt = open(os.path.join(
            os.getcwd(), 'test', 'fixtures', 'transcript.txt'
        )).read()

        self.driver.execute_script("$('%s').val('%s');" % (
            selector,
            transcript_txt.replace("'", r"\'").replace('\n', r'\n')
        ))
        textarea.send_keys('\n')

        wait = WebDriverWait(self.driver, 2)
        wait.until(EC.title_contains('Joe Chengsen'))

    def _assert_profile_page_state(self):
        self._wait_for_element('.course-content')

        course_contents = self._css_all(".course-content")
        self.assertEqual(len(course_contents), 48)
        self.assertTrue(course_contents[0].text.startswith("CS 444"))

    def _paste_schedule(self):
        schedule_txt = open(os.path.join(
            os.getcwd(), 'test', 'fixtures', 'schedule.txt'
        )).read()

        import_schedule_link = self._css('#import-schedule-heading')
        import_schedule_link.click()

        selector = ".schedule-input-textarea"
        self._wait_for_element(selector)
        textarea = self._css(selector)
        self.driver.execute_script("$('%s').val('%s');" % (
            selector,
            schedule_txt.replace("'", r"\'").replace('\n', r'\n')
        ))
        textarea.send_keys('\n')

        alert = self.driver.switch_to_alert()
        alert.accept()

        self._wait_for_element('button.curr-week-btn')

    def test_onboarding(self):
        self.driver.get('http://localhost:5001/')

        self._assert_homepage_state()

        user_count_pre = m.User.objects.count()
        self._login()
        self.assertEqual(m.User.objects.count(), user_count_pre + 1)

        uc_count_pre = m.UserCourse.objects.count()
        self._paste_transcript()
        self.assertEqual(m.UserCourse.objects.count(), uc_count_pre + 48)

        self._assert_profile_page_state()

        usi_count_pre = m.UserScheduleItem.objects.count()
        self._paste_schedule()
        self.assertEqual(m.UserScheduleItem.objects.count(),
                         usi_count_pre + 162)
