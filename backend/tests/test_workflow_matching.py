import unittest
from types import SimpleNamespace

from app.services.workflow_matching import match_workflows


class WorkflowMatchingTests(unittest.TestCase):
    def test_field_order_does_not_change_score(self):
        source = SimpleNamespace(schema_={"amount": {"type": "number"}, "region": {"type": "text"}})
        workflows = [SimpleNamespace(id=1, name="通报", mode="formula", template_id=2, column_mapping={"A": "region", "B": "amount"})]
        templates = [SimpleNamespace(id=2, version="1.0")]
        self.assertEqual(match_workflows(source, workflows, templates)[0]["score"], 1.0)
