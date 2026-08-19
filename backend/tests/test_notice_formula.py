import unittest

from app.services.notice_formula import emit_notice_formulas


class NoticeFormulaTests(unittest.TestCase):
    def test_emits_sumifs_ratio_and_rank(self):
        formulas = emit_notice_formulas({
            "dimensions": {"source_field": "BA", "rule_field": "AZ", "rule_value": "发展人"},
            "rows": [{"row": 5, "key": "邓州"}, {"row": 6, "key": "镇平"}],
            "metrics": {
                "daily": {"column": "E", "source_field": "W", "aggregate": "sum"},
                "rate": {"column": "F", "kind": "ratio", "source_metric": "daily"},
                "rank": {"column": "J", "kind": "rank", "source_metric": "daily"},
            },
        })
        self.assertIn("SUMIFS", formulas["5"]["daily"])
        self.assertIn("AZ", formulas["5"]["daily"])
        self.assertEqual(formulas["5"]["rate"], "=IFERROR(E5/D5,0)")
        self.assertIn("RANK(E5,$E$5:$E$6,0)", formulas["5"]["rank"])


if __name__ == "__main__":
    unittest.main()
