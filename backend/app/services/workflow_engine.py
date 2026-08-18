from copy import copy
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.formula.translate import Translator


class WorkflowEngine:
    def __init__(self, template_path: str):
        self.workbook = load_workbook(template_path, read_only=False, data_only=False)

    def execute_formula_mode(self, data: list[dict], column_mapping: dict[str, str]):
        for worksheet in self.workbook.worksheets:
            mappings = self._sheet_mappings(worksheet.title, column_mapping)
            for row_number, record in enumerate(data, start=2):
                for column, field in mappings.items():
                    cell = worksheet[f"{column}{row_number}"]
                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        continue
                    self._write_preserving_style(cell, record.get(field))
                self._fill_formulas(worksheet, row_number)
        self.workbook.calculation.fullCalcOnLoad = True
        self.workbook.calculation.forceFullCalc = True
        return self.workbook

    @staticmethod
    def _sheet_mappings(sheet_title: str, mapping: dict[str, str]) -> dict[str, str]:
        qualified = {key.split("!", 1)[1]: value for key, value in mapping.items() if key.startswith(f"{sheet_title}!")}
        if qualified:
            return qualified
        if sheet_title == mapping.get("__sheet__", "") or sheet_title == "":
            return {key: value for key, value in mapping.items() if "!" not in key and not key.startswith("__")}
        return {key: value for key, value in mapping.items() if "!" not in key and not key.startswith("__")}

    def _fill_formulas(self, worksheet, row_number: int) -> None:
        if row_number <= 2:
            return
        for column in range(1, worksheet.max_column + 1):
            source = worksheet.cell(row=2, column=column)
            target = worksheet.cell(row=row_number, column=column)
            if isinstance(source.value, str) and source.value.startswith("=") and target.value is None:
                target.value = self.translate_formula(source.value, source.coordinate, target.coordinate)
                target._style = copy(source._style)

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
