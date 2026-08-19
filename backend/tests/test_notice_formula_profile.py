import unittest
from pathlib import Path

from app.services.notice_formula_profile import extract_notice_formula_profile


class NoticeFormulaProfileTests(unittest.TestCase):
    def test_extracts_real_formula_semantics(self):
        path = Path(__file__).parents[2] / ".monkeycode-tmp-files" / "8f114b12-模版+明细 - 副本.xlsx"
        if not path.exists():
            self.skipTest("公式样例未上传")
        profile = extract_notice_formula_profile(str(path))
        self.assertEqual(profile["dimensions"]["source_column"], "BA")
        self.assertIsNone(profile["dimensions"]["rule_field"])
        self.assertEqual(profile["metrics"]["daily"]["date"]["column"], "B")
        self.assertNotIn("date", profile["metrics"]["original"])
        self.assertEqual(profile["metrics"]["product_daily"]["filters"][0]["value"], "升档专用合约")
        self.assertNotIn("date", profile["metrics"]["product_monthly"])
        self.assertEqual(profile["metrics"]["rank"]["rank_ranges"][0]["first"], 5)
        self.assertEqual(profile["metrics"]["rank"]["rank_ranges"][0]["last"], 15)


if __name__ == "__main__":
    unittest.main()
