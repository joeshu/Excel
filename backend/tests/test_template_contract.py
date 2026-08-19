import unittest

from app.services.template_contract import validate_native_contract


class TemplateContractTests(unittest.TestCase):
    def test_validates_required_fields_for_native_workflow(self):
        profile = {"field_contract": {"required": ["日期", "金额"]}}
        result = validate_native_contract(profile, {}, {"日期", "金额", "单位"})
        self.assertTrue(result["valid"])
        self.assertEqual(result["missing_fields"], [])

    def test_reports_missing_fields(self):
        profile = {"field_contract": {"required": ["日期", "金额"]}}
        result = validate_native_contract(profile, {}, {"日期"})
        self.assertFalse(result["valid"])
        self.assertEqual(result["missing_fields"], ["金额"])


if __name__ == "__main__":
    unittest.main()
