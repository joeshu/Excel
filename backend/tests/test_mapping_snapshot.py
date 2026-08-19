import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.routers.workflows import create_mapping_snapshot


class MappingSnapshotTests(unittest.TestCase):
    def test_snapshot_creation_requires_valid_mapping(self):
        workflow = SimpleNamespace(id=7, template_id=3)
        template = SimpleNamespace(id=3, version="1.0", column_meta={"sheets": [{"title": "通报", "columns": [{"column": "A", "header": "地区", "type": "text"}]}]})
        source = SimpleNamespace(id=4, field_signature="地区", schema_={"地区": {"type": "str"}})
        db = Mock()
        db.get.side_effect = lambda model, key: {7: workflow, 3: template, 4: source}.get(key)
        db.refresh.side_effect = lambda item: setattr(item, "id", 1)
        result = create_mapping_snapshot(7, SimpleNamespace(data_source_id=4, rules=[{"target": "通报!A", "source_kind": "field", "source_field": "地区"}]), db)
        self.assertEqual(result.template_version, "1.0")
        self.assertEqual(result.dependency_order, [])
        db.add.assert_called_once()


if __name__ == "__main__":
    unittest.main()
