import datetime

import rmc.models as m
import rmc.test.lib as testlib


class SimpleCourseAlert(m.BaseCourseAlert):
    def send_alert(self, sections):
        return True


class BaseCourseAlertTest(testlib.FixturesTestCase):
    def tearDown(self):
        # Clear DB for other tests
        SimpleCourseAlert.objects.delete()
        super(BaseCourseAlertTest, self).tearDown()

    def test_send_eligible_alerts(self):
        # This class is full. Should not alert anything.
        alert = SimpleCourseAlert(
            course_id='spcom223',
            created_date=datetime.datetime.now(),
            expiry_date=datetime.datetime.max,
            term_id='2014_01',
            section_type='LEC',
            section_num='003',
        )
        alert.save()

        alerts_sent = SimpleCourseAlert.send_eligible_alerts()
        self.assertEqual(alerts_sent, 0)
        self.assertEqual(SimpleCourseAlert.objects.count(), 1)

        # Here's a non-full class to alert on.
        alert = SimpleCourseAlert(
            course_id='spcom223',
            created_date=datetime.datetime.now(),
            expiry_date=datetime.datetime.max,
            term_id='2014_01',
            section_type='LEC',
            section_num='002',
        )
        alert.save()

        self.assertEqual(SimpleCourseAlert.objects.count(), 2)

        alerts_sent = SimpleCourseAlert.send_eligible_alerts()
        self.assertEqual(alerts_sent, 1)
        self.assertEqual(SimpleCourseAlert.objects.count(), 1)

        # Here's a less restrictive query with multiple available sections
        alert = SimpleCourseAlert(
            course_id='spcom223',
            created_date=datetime.datetime.now(),
            expiry_date=datetime.datetime.max,
        )
        alert.save()

        self.assertEqual(SimpleCourseAlert.objects.count(), 2)

        alerts_sent = SimpleCourseAlert.send_eligible_alerts()
        self.assertEqual(alerts_sent, 1)
        self.assertEqual(SimpleCourseAlert.objects.count(), 1)

    def test_delete_expired(self):
        self.assertEqual(SimpleCourseAlert.objects.count(), 0)

        SimpleCourseAlert(
            course_id='spcom223',
            created_date=datetime.datetime.now(),
            expiry_date=datetime.datetime.min,
        ).save()
        SimpleCourseAlert(
            course_id='cs241',
            created_date=datetime.datetime.now(),
            expiry_date=datetime.datetime.max,
        ).save()

        self.assertEqual(SimpleCourseAlert.objects.count(), 2)

        SimpleCourseAlert.delete_expired()
        self.assertEqual(SimpleCourseAlert.objects.count(), 1)
        self.assertEqual(SimpleCourseAlert.objects[0].course_id, 'cs241')
