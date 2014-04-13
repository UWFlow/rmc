import unittest

from processor import group_similar_exam_sections


class ExamTest(unittest.TestCase):
    def test_group_similar_exam_sections_one_section(self):
        self.assertEquals(group_similar_exam_sections(
            [
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '007',
                }
            ]), 
            [
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '007',
                }
            ]
        )

    def test_group_similar_exam_sections_two_sections(self):
        self.assertEquals(group_similar_exam_sections(
            [
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '007',
                },
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '001',
                }
            ]), 
            [
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '001, 007',
                }
            ]
        )

    def test_group_different_exam_sections_three_sections(self):
        self.assertEquals(group_similar_exam_sections(
            [
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '007',
                },
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '001',
                },
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'MC',
                    'section': '117',
                }
            ]), 
            [
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'DC',
                    'section': '001, 007',
                },
                {
                    'start-time': '4:00 PM',
                    'end-time': '7:00 PM',
                    'location': 'MC',
                    'section': '117',
                }
            ]
        )

