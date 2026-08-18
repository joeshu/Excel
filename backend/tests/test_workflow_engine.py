import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook

from app.services.workflow_engine import WorkflowEngine


class WorkflowEngineTests(unittest.TestCase):
    def create_template(self) -> tuple[Path, tempfile.TemporaryDirectory]:
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "template.xlsx"
        workbook = Workbook()
        first = workbook.active
        first.title = "销售明细"
        first.append(["名称", "数量", "金额"])
        first.append([None, None, "=B2*10"])
        second = workbook.create_sheet("汇总")
        second.append(["名称"])
        second.append([None])
        workbook.save(path)
        return path, directory

    def test_fills_multiple_sheets_and_formula_rows(self):
        template, directory = self.create_template()
        self.addCleanup(directory.cleanup)
        engine = WorkflowEngine(str(template))
        engine.execute_formula_mode(
            [{"name": "A", "quantity": 2}, {"name": "B", "quantity": 3}],
            {"销售明细!A": "name", "销售明细!B": "quantity", "汇总!A": "name"},
        )
        output = Path(directory.name) / "output.xlsx"
        engine.save(str(output))
        workbook = load_workbook(output, data_only=False)
        self.assertEqual(workbook["销售明细"]["A2"].value, "A")
        self.assertEqual(workbook["销售明细"]["A3"].value, "B")
        self.assertEqual(workbook["销售明细"]["C3"].value, "=B3*10")
        self.assertEqual(workbook["汇总"]["A2"].value, "A")
        self.assertEqual(workbook["汇总"]["A3"].value, "B")

    def test_legacy_unqualified_mapping_only_writes_first_sheet(self):
        template, directory = self.create_template()
        self.addCleanup(directory.cleanup)
        engine = WorkflowEngine(str(template))
        engine.execute_formula_mode([{"name": "A"}], {"A": "name"})
        self.assertEqual(engine.workbook["销售明细"]["A2"].value, "A")
        self.assertIsNone(engine.workbook["汇总"]["A2"].value)


if __name__ == "__main__":
    unittest.main()
