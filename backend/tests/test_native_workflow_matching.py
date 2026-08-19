import unittest
from types import SimpleNamespace

from app.services.workflow_matching import match_workflows


class NativeWorkflowMatchingTests(unittest.TestCase):
    def test_native_workflow_uses_saved_template_profile_fields(self):
        source = SimpleNamespace(schema_={"日期": {}, "金额": {}})
        workflow = SimpleNamespace(id=1, name="原生通报", template_id=3, mode="template_native", column_mapping={})
        template = SimpleNamespace(id=3, version="1.0", column_meta={"native_profile": {"field_contract": {"required": ["日期", "金额", "单位"]}}})
        result = match_workflows(source, [workflow], [template])[0]
        self.assertEqual(result["matched_fields"], ["日期", "金额"])
        self.assertEqual(result["missing_fields"], ["单位"])
        self.assertLess(result["score"], 1)


if __name__ == "__main__":
    unittest.main()
