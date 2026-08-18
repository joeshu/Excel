import unittest

from app.services.output_naming import final_output_name


class OutputNamingTests(unittest.TestCase):
    def test_name_contains_readable_notice_metadata(self):
        name = final_output_name(7, "abcdef123456", {"title": "月度/通报", "as_of_date": "2026/08/18"})
        self.assertEqual(name, "月度_通报_2026-08-18_abcdef12_task7.xlsx")

    def test_name_has_safe_defaults(self):
        self.assertEqual(final_output_name(2, None, {}), "Excel通报_未定日期_single_task2.xlsx")
