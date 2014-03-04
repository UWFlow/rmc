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
