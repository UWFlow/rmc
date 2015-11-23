import rmc.models as m
import rmc.test.lib as testlib


class ProfessorTest(testlib.FixturesTestCase):

    def test_transfer_reviews_from(self):
        real_prof = m.Professor(
            id='real_prof'
        )
        dupe_prof = m.Professor(
            id='dupe_prof'
        )

        DUPE_PROF_REVIEWS_START_NUM = 5

        for i in range(DUPE_PROF_REVIEWS_START_NUM):
            m.MenloCourse(
                professor_id=dupe_prof.id,
                course_id='cs135'
            ).save()

        self.assertEqual(
            len(m.MenloCourse.objects(professor_id=real_prof.id)),
            0
        )
        self.assertEqual(
            len(m.MenloCourse.objects(professor_id=dupe_prof.id)),
            DUPE_PROF_REVIEWS_START_NUM
        )

        real_prof.transfer_reviews_from(dupe_prof)

        self.assertEqual(
            len(m.MenloCourse.objects(professor_id=real_prof.id)),
            DUPE_PROF_REVIEWS_START_NUM
        )
        self.assertEqual(
            len(m.MenloCourse.objects(professor_id=dupe_prof.id)),
            0
        )
