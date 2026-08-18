import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from app.services.formula_service import function_names, python_aggregate, referenced_sheets, validate_formulas


class FormulaServiceTests(unittest.TestCase):
    def test_formula_functions_and_sheet_references(self):
        formula = '=IFERROR(VLOOKUP(A2,\'客户字典\'!$A:$B,2,FALSE),"未匹配")'
        self.assertEqual(function_names(formula), ["IFERROR", "VLOOKUP"])
        self.assertEqual(referenced_sheets(formula), ["客户字典"])

    def test_python_aggregate_matches_sumifs_countifs_shape(self):
        records = [{"region": "华东", "amount": 10, "risk": "正常"}, {"region": "华东", "amount": 5, "risk": "复核"}, {"region": "华南", "amount": 8, "risk": "正常"}]
        rows = python_aggregate(records, "region", "amount", {"risk": "正常"})
        self.assertEqual(rows, [{"group": "华东", "count": 1, "sum": 10.0}, {"group": "华南", "count": 1, "sum": 8.0}])

    def test_missing_sheet_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "formula.xlsx"
            workbook = Workbook()
            workbook.active["A1"] = "=SUMIFS(不存在!A:A,A:A,1)"
            workbook.save(path)
            result = validate_formulas(str(path))
            self.assertFalse(result["valid"])
            self.assertEqual(result["issues"][0]["type"], "missing_sheet")
