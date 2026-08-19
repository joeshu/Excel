import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.routers.workflows import create_mapping_rule, get_mapping_rule_version, list_mapping_rule_versions


class MappingRuleVersionTests(unittest.TestCase):
    def _database(self):
        workflow = SimpleNamespace(id=7, template_id=3)
        template = SimpleNamespace(id=3, version="2.0", column_meta={"sheets": [{"title": "通报", "columns": [{"column": "A", "header": "地区", "type": "text"}]}]})
        source = SimpleNamespace(id=4, field_signature="地区", schema_={"地区": {"type": "str"}})
        db = Mock()
        db.get.side_effect = lambda model, key: {7: workflow, 3: template, 4: source}.get(key)
        db.scalar.side_effect = [2]
        db.refresh.side_effect = lambda item: setattr(item, "id", 11)
        return db

    def test_create_increments_version_and_binds_template(self):
        db = self._database()
        result = create_mapping_rule(7, SimpleNamespace(data_source_id=4, rules=[{"target": "通报!A", "source_kind": "field", "source_field": "地区"}]), db)
        self.assertEqual(result.version, 3)
        self.assertEqual(result.template_version, "2.0")
        db.add.assert_called_once()

    def test_list_versions_queries_workflow(self):
        db = Mock()
        db.get.return_value = SimpleNamespace(id=7)
        db.scalars.return_value.all.return_value = [SimpleNamespace(version=2), SimpleNamespace(version=1)]
        result = list_mapping_rule_versions(7, db)
        self.assertEqual([item.version for item in result], [2, 1])

    def test_get_version_raises_for_unknown_version(self):
        db = Mock()
        db.scalar.return_value = None
        with self.assertRaises(Exception):
            get_mapping_rule_version(7, 9, db)


if __name__ == "__main__":
    unittest.main()
