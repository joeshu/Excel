import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from app.services.workbook_preview import preview_workbook


class WorkbookPreviewTests(unittest.TestCase):
    def test_previews_all_final_workbook_sheets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "final.xlsx"
            workbook = Workbook()
            workbook.active.title = "通报表"
            workbook.active.append(["标题", "值"])
            workbook.active.append(["测试", 1])
            workbook.create_sheet("工作流配置").append(["配置项", "值"])
            workbook.save(path)
            result = preview_workbook(str(path), limit=10)
            self.assertEqual(result["sheet_count"], 2)
            self.assertEqual([sheet["title"] for sheet in result["sheets"]], ["通报表", "工作流配置"])
            self.assertEqual(result["sheets"][0]["rows"][1][1], 1)
