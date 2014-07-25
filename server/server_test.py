import json

import werkzeug.datastructures as datastructures

import rmc.models as m
import rmc.test.lib as testlib


class ServerTest(testlib.FlaskTestCase):
    def tearDown(self):
        # Clear DB for other tests
        super(ServerTest, self).tearDown()

    def get_csrf_token_header(self):
        resp = self.app.get('/api/v1/csrf-token')
        headers = datastructures.Headers()
        headers.add('X-CSRF-Token', json.loads(resp.get_data())['token'])
        return headers

    def test_remove_user_course(self):
        data = {
            'user_id': '53d28ad4c4866e68b440f113',
            'api_key': 'qwerty123',
            'term_id': '2014_09',
            'course_id': 'math137',
        }

        orig_usi_count = m.UserScheduleItem.objects.count()

        self.assertEquals(m.UserCourse.objects(
            user_id=data['user_id'],
            term_id=data['term_id'],
            course_id=data['course_id'],
        ).count(), 1)

        self.assertEquals(m.UserScheduleItem.objects(
            user_id=data['user_id'],
            term_id=data['term_id'],
            course_id=data['course_id'],
        ).count(), 38)

        self.assertEquals(
            len(m.User.objects.with_id(data['user_id']).course_history), 52)

        headers = self.get_csrf_token_header()
        resp = self.app.post(
                '/api/user/remove_course', data=data, headers=headers)

        self.assertResponseOk(resp)

        self.assertEquals(m.UserCourse.objects(
            user_id=data['user_id'],
            term_id=data['term_id'],
            course_id=data['course_id'],
        ).count(), 0)

        self.assertEquals(m.UserScheduleItem.objects(
            user_id=data['user_id'],
            term_id=data['term_id'],
            course_id=data['course_id'],
        ).count(), 0)

        self.assertEquals(
            orig_usi_count - m.UserScheduleItem.objects.count(), 38)

        self.assertEquals(
            len(m.User.objects.with_id(data['user_id']).course_history), 51)
