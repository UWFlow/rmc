import rmc.models as m
import rmc.test.lib as testlib


class ProfessorTest(testlib.FixturesTestCase):

    def transfer_reviews_from_prof_helper(self, delete_prof):
        real_prof = m.Professor(
            id='real_prof'
        )
        dupe_prof = m.Professor(
            id='dupe_prof',
            first_name='first',
            last_name='last'
        )
        dupe_prof.save()

        NUM_DUPE_PROF_REVIEWS = 5

        for i in range(NUM_DUPE_PROF_REVIEWS):
            m.MenloCourse(
                professor_id=dupe_prof.id,
                course_id='cs135'
            ).save()

        self.assertEqual(
            m.MenloCourse.objects(professor_id=real_prof.id).count(), 0
        )
        self.assertEqual(
            m.MenloCourse.objects(professor_id=dupe_prof.id).count(),
            NUM_DUPE_PROF_REVIEWS
        )

        real_prof.transfer_reviews_from_prof(dupe_prof, delete_prof)

        self.assertEqual(
            m.MenloCourse.objects(professor_id=real_prof.id).count(),
            NUM_DUPE_PROF_REVIEWS
        )
        self.assertEqual(
            m.MenloCourse.objects(professor_id=dupe_prof.id).count(), 0
        )
        self.assertEqual(
            m.Professor.objects(id=dupe_prof.id).count(),
            0 if delete_prof else 1
        )

        #clean up
        m.Professor.objects.delete()
        m.MenloCourse.objects.delete()

    def test_transfer_reviews_from_prof(self):
        self.transfer_reviews_from_prof_helper(True)
        self.transfer_reviews_from_prof_helper(False)
