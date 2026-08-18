from copy import copy
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.formula.translate import Translator


class WorkflowEngine:
    def __init__(self, template_path: str):
        self.workbook = load_workbook(template_path, read_only=False, data_only=False)

    def execute_formula_mode(self, data: list[dict], column_mapping: dict[str, str]):
        worksheet = self.workbook.worksheets[0]
        for row_number, record in enumerate(data, start=2):
            for column, field in column_mapping.items():
                cell = worksheet[f"{column}{row_number}"]
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    continue
                self._write_preserving_style(cell, record.get(field))
        self.workbook.calculation.fullCalcOnLoad = True
        self.workbook.calculation.forceFullCalc = True
        return self.workbook

    @staticmethod
    def _write_preserving_style(cell, value) -> None:
        style = copy(cell._style)
        cell.value = value
        cell._style = style

    def save(self, output_path: str) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        self.workbook.save(output_path)
        return output_path

    @staticmethod
    def translate_formula(formula: str, origin: str, target: str) -> str:
        return Translator(formula, origin=origin).translate_formula(target)
