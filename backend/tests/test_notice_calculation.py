import unittest

from app.services.notice_calculation import calculate_notice


class NoticeCalculationTests(unittest.TestCase):
    def test_progressive_rate_matches_formula_semantics(self):
        config = {
            "dimensions": {"source_field": "BA"},
            "rows": [{"row": 5, "key": "甲", "target": 100}],
            "metrics": {
                "original": {"column": "G", "source_field": "amount", "dimension_field": "BA", "aggregate": "sum"},
                "sequential_rate": {"column": "I", "kind": "derived", "formula": "progressive_rate", "source_metric": "original", "denominator": "target", "total_days": 31, "elapsed_days": 10},
            },
        }
        result = calculate_notice([{"BA": "甲", "amount": 50}], config)
        self.assertEqual(result["values"]["5"]["sequential_rate"], 1.55)
    def setUp(self):
        self.records = [
            {"BA": "邓州", "AZ": "发展人", "A": "20260731", "C": "升档专用合约", "W": 10, "ID": "1"},
            {"BA": "邓州", "AZ": "发展人", "A": "20260731", "C": "升档无合约", "W": 5, "ID": "2"},
            {"BA": "镇平", "AZ": "发展人", "A": "20260731", "C": "升档专用合约", "W": 7, "ID": "3"},
            {"BA": "邓州", "AZ": "其他", "A": "20260731", "C": "升档专用合约", "W": 99, "ID": "4"},
        ]

    def test_ba_and_az_drive_metric_filters(self):
        result = calculate_notice(self.records, {
            "dimensions": {"source_field": "BA", "rule_field": "AZ", "rule_value": "发展人"},
            "rows": [{"row": 5, "key": "邓州"}, {"row": 6, "key": "镇平"}],
            "metrics": {"daily": {"source_field": "W", "aggregate": "sum", "dimension_field": "BA", "date": {"field": "A", "value": "20260731"}}},
        })
        self.assertEqual(result["values"]["5"]["daily"], 15)
        self.assertEqual(result["values"]["6"]["daily"], 7)
        self.assertEqual(result["matched_rows"], 3)

    def test_ratio_rank_and_total(self):
        result = calculate_notice(self.records[:3], {
            "dimensions": {"source_field": "BA", "rule_field": "AZ", "rule_value": "发展人"},
            "rows": [{"row": 5, "key": "邓州"}, {"row": 6, "key": "镇平"}],
            "metrics": {
                "actual": {"source_field": "W", "aggregate": "sum", "dimension_field": "BA"},
                "target": {"source_field": "W", "aggregate": "count", "dimension_field": "BA"},
                "rate": {"kind": "ratio", "numerator": "actual", "denominator": "target"},
                "rank": {"kind": "rank", "source_metric": "actual"},
            },
        })
        self.assertEqual(result["values"]["5"]["rank"], 1)
        self.assertEqual(result["values"]["6"]["rank"], 2)
        self.assertEqual(result["totals"]["actual"], 22)


if __name__ == "__main__":
    unittest.main()
