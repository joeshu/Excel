import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.routers.data_sources import data_source_mapping_fields
from app.routers.templates import get_workbook_profile, save_workbook_profile, template_mapping_schema


class MappingRouteTests(unittest.TestCase):
    def test_template_mapping_schema_returns_normalized_columns(self):
        template = SimpleNamespace(id=3, version="2.0", name="通报模板", column_meta={"sheets": [{"title": "通报", "columns": [{"column": "A", "header": "地区", "type": "text", "formula": None}]}]})
        db = Mock()
        db.get.return_value = template
        result = template_mapping_schema(3, db)
        self.assertEqual(result["template_version"], "2.0")
        self.assertEqual(result["columns"][0]["target"], "通报!A")

    def test_data_source_mapping_fields_returns_normalized_fields(self):
        source = SimpleNamespace(id=4, name="基础数据", field_signature="地区,金额", schema_={"地区": {"type": "str"}, "金额": {"type": "float"}})
        db = Mock()
        db.get.return_value = source
        result = data_source_mapping_fields(4, db)
        self.assertEqual([item["field"] for item in result["fields"]], ["地区", "金额"])
        self.assertEqual(result["fields"][1]["type"], "number")

    def test_workbook_profile_is_persisted_per_template(self):
        template = SimpleNamespace(id=8, version="3.0", column_meta={})
        stored = SimpleNamespace(template_id=8, profile={"detail_sheet": "明细"}, updated_at="now")
        db = Mock()
        db.get.return_value = template
        db.scalar.side_effect = [None, stored]
        result = save_workbook_profile(8, {"detail_sheet": "明细", "data_start_row": 4}, db)
        self.assertEqual(result["profile"]["data_start_row"], 4)
        self.assertEqual(stored.profile["detail_sheet"], "明细")
        self.assertEqual(db.add.call_count, 1)


if __name__ == "__main__":
    unittest.main()
