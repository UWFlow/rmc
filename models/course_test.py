import rmc.models as m
import rmc.test.lib as testlib


class CourseTest(testlib.FixturesTestCase):

    def assertResultsEquals(self, results, expected):
        self.assertItemsEqual([course['id'] for course in results], expected)

    def test_search(self):
        # Test empty search
        results, has_more = m.Course.search({})
        self.assertResultsEquals(results, ['econ101', 'math135', 'psych101',
                'econ102', 'math137', 'afm131', 'chem120', 'math138', 'soc101',
                'econ201'])

        # Test keywords param
        results, has_more = m.Course.search({'keywords': 'cs'})
        self.assertResultsEquals(results, ['cs241', 'cs245', 'cs135', 'cs350',
                'cs246', 'cs240', 'cs341', 'cs136', 'cs115', 'cs348'])

        # Test count param
        results, has_more = m.Course.search({'count': 5})
        self.assertEquals(len(results), 5)
        self.assertTrue(has_more)

        # Test offset param
        results, has_more = m.Course.search({'offset': 5})
        self.assertResultsEquals(results, ['afm131', 'chem120', 'math138',
                'soc101', 'econ201', 'stat230', 'afm101', 'math136', 'math115',
                'stat231'])

        # Test sort modes

        results, has_more = m.Course.search({'sort_mode': 'interesting'})
        self.assertResultsEquals(results, ['music140', 'math145', 'math147',
               'mte320', 'cs488', 'cs241', 'kin100', 'psych253', 'cs137',
               'fr192a'])

        results, has_more = m.Course.search({'sort_mode': 'easy'})
        self.assertResultsEquals(results, ['clas104', 'intst101', 'rec100',
                'psych211', 'mthel100', 'clas100', 'music140', 'ital101',
                'sci206', 'clas202'])

        results, has_more = m.Course.search({'sort_mode': 'hard'})
        self.assertResultsEquals(results, ['phys234', 'ece370', 'ece126',
                'biol441', 'ece105', 'syde283', 'ece242', 'cs457', 'phys263',
                'se380'])

        results, has_more = m.Course.search({'sort_mode': 'course code'})
        self.assertResultsEquals(results, ['acc604', 'acc605', 'acc606',
                'acc607', 'acc608', 'acc609', 'acc610', 'acc611', 'acc620',
                'acc621'])

        # Friends taken should default to popular if no current user given.
        results_friends_taken, has_more = m.Course.search({
            'sort_mode': 'friends_taken'
        })
        results_popular, has_more = m.Course.search({'sort_mode': 'popular'})
        self.assertResultsEquals(results_friends_taken,
                [course['id'] for course in results_popular])

        # Test direction param
        results, has_more = m.Course.search({
            'sort_mode': 'course code',
            'direction': -1
        })
        self.assertResultsEquals(results, ['ws499b', 'ws499a', 'ws475',
                'ws430', 'ws422', 'ws409', 'ws370', 'ws365', 'ws350', 'ws347'])

        # TODO(david): Add tests for searching when there's a current_user
