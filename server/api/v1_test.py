import rmc.test.lib as testlib


class V1Test(testlib.FlaskTestCase):
    def test_get_course(self):
        resp = self.app.get('/api/v1/courses/cs444')
        self.assertResponseOk(resp)
        self.assertJsonResponse(resp, {
            'code': 'CS 444',
            'description': 'Phases of compilation. Lexical analysis and '
                'a review of parsing. Compiler-compilers and translator '
                'writing systems. LEX and YACC. Scope rules, block structure, '
                'and symbol tables. Runtime stack management. Parameter '
                'passage mechanisms. Stack storage organization and '
                'templates. Heap storage management. Intermediate code. '
                'Code generation. Macros.',
            'id': 'cs444',
            'name': 'Compiler Construction',
            'overall': {'count': 7, 'rating': 0.8571428571428571},
            'prereqs': 'CS350 or SE350; Computer Science students only',
            'professor_ids': ['gordon_cormack', 'ondrej_lhotak'],
            'ratings': [{'count': 3, 'name': 'usefulness', 'rating': 1.0},
                        {'count': 5, 'name': 'easiness', 'rating': 0.6},
                        {'count': 5, 'name': 'interest', 'rating': 0.8}],
            'reviews': []})

    def test_search_course(self):
        # Most of the search functionality is exercised in course_test.py, so
        # there's just one test here.
        resp = self.app.get('/api/v1/search/courses'
                '?keywords=cs&sort_mode=hard&count=1&&offset=4')
        self.assertResponseOk(resp)
        self.assertJsonResponse(resp, {
            'has_more': True,
            'courses': [{
                'ratings': [
                    {
                        'count': 1,
                        'rating': 1.0,
                        'name': 'usefulness'
                    },
                    {
                        'count': 72,
                        'rating': 0.19444444444444445,
                        'name': 'easiness'
                    },
                    {
                        'count': 40,
                        'rating': 0.625,
                        'name': 'interest'
                    }
                ],
                'code': 'CS 448',
                'name': 'Database Systems Implementation',
                'overall': {
                    'count': 47,
                    'rating': 0.702127659574468
                },
                'professor_ids': ['edward_chan', 'ian_davis', 'david_toman',
                    'lei_chen', 'tamer_ozsu', 'grant_weddell', 'ihab_ilyas',
                    'kenneth_salem'],
                'prereqs': 'CS348 and ( CS350 or SE350); Computer Science '
                    'students only',
                'id': 'cs448',
                'description': 'The objective of this course is to introduce '
                    'students to fundamentals of building a relational '
                    'database management system. The course focuses on the '
                    'database engine core technology by studying topics such '
                    'as storage management (data layout, disk-based data '
                    'structures), indexing, query processing algorithms, '
                    'query optimization, transactional concurrency control, '
                    'logging and recovery.'
                }
            ],
            'user_courses': []
        })

# TODO(david): More tests!
