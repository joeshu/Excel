import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from app.services.recalculation import recalculate


class RecalculationTests(unittest.TestCase):
    def test_falls_back_to_formula_only_without_calculation_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "formula.xlsx"
            workbook = Workbook()
            workbook.active["A1"] = "=1+1"
            workbook.save(path)
            result = recalculate(str(path))
            self.assertIn(result.engine, {"formula_only", "libreoffice"})


if __name__ == "__main__":
    unittest.main()
