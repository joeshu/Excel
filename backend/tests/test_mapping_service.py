import unittest
from types import SimpleNamespace

from app.services.mapping_service import extract_formula_dependencies, infer_formula_type, recommend_mapping, validate_mapping


class MappingServiceTests(unittest.TestCase):
    def setUp(self):
        self.columns = [
            {"target": "通报!A", "header": "地区", "type": "text", "is_formula": False},
            {"target": "通报!B", "header": "金额", "type": "number", "is_formula": False},
            {"target": "通报!C", "header": "合计", "type": "formula", "is_formula": True, "formula": "=B2*2"},
        ]
        self.fields = [{"field": "地区", "type": "text"}, {"field": "金额", "type": "number"}]

    def test_recommendation_prefers_exact_header_match(self):
        result = recommend_mapping(self.columns, self.fields)
        self.assertEqual(result[0]["candidates"][0]["field"], "地区")
        self.assertEqual(result[2]["status"], "locked")

    def test_formula_dependencies_are_extracted(self):
        self.assertEqual(extract_formula_dependencies("金额 * 2"), (["金额"], None))
        self.assertEqual(extract_formula_dependencies("金额 *" )[1], "invalid syntax")

    def test_formula_result_type_is_inferred_from_dependencies(self):
        self.assertEqual(infer_formula_type("金额 * 2", {"金额": "number"}), ("number", None))
        self.assertEqual(infer_formula_type('地区 + "-"', {"地区": "text"}), ("text", None))
        result_type, error = infer_formula_type("地区 * 2", {"地区": "text"})
        self.assertEqual(result_type, "unknown")
        self.assertIn("类型兼容", error)

    def test_validation_requires_all_non_formula_columns(self):
        result = validate_mapping(self.columns, self.fields, [{"target": "通报!A", "source_kind": "field", "source_field": "地区"}])
        self.assertFalse(result["valid"])
        self.assertIn("通报!B", {item["target"] for item in result["errors"]})

    def test_validation_rejects_template_formula_override(self):
        result = validate_mapping(self.columns, self.fields, [
            {"target": "通报!A", "source_kind": "field", "source_field": "地区"},
            {"target": "通报!B", "source_kind": "field", "source_field": "金额"},
            {"target": "通报!C", "source_kind": "field", "source_field": "金额"},
        ])
        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"][0]["type"], "template_formula_locked")

    def test_validation_detects_formula_cycle(self):
        result = validate_mapping(self.columns[:2], [{"field": "A", "type": "number"}], [
            {"target": "A", "source_kind": "formula", "expression": "B + 1"},
            {"target": "B", "source_kind": "formula", "expression": "A + 1"},
        ])
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["type"] == "circular_dependency" for item in result["errors"]))

    def test_validation_returns_field_quality_and_formula_type(self):
        result = validate_mapping(
            [{"target": "通报!A", "header": "合计", "type": "number", "is_formula": False}],
            [{"field": "金额", "type": "number", "nullable": True, "non_empty_rate": 0.5, "sample_values": [1]}],
            [{"target": "通报!A", "source_kind": "formula", "expression": "金额 * 2"}],
        )
        self.assertEqual(result["field_quality"]["金额"]["status"], "warning")
        self.assertEqual(result["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
