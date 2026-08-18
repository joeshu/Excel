from pathlib import Path

from openpyxl import load_workbook


class TemplateParser:
    def parse(self, file_path: str) -> dict:
        workbook = load_workbook(file_path, read_only=False, data_only=False)
        sheets = []
        has_formula = False
        for worksheet in workbook.worksheets:
            columns = []
            for cell in worksheet[1]:
                values = []
                for row in worksheet.iter_rows(min_row=2, min_col=cell.column, max_col=cell.column):
                    value = row[0].value
                    if value is not None:
                        values.append(value)
                formula = None
                formula_row = None
                for row in range(2, worksheet.max_row + 1):
                    value = worksheet.cell(row=row, column=cell.column).value
                    if isinstance(value, str) and value.startswith("="):
                        formula = value
                        formula_row = row
                        break
                if formula:
                    has_formula = True
                columns.append({
                    "column": cell.column_letter,
                    "header": cell.value,
                    "type": self._infer_type(values, formula),
                    "formula": formula,
                    "formula_row": formula_row,
                    "number_format": cell.number_format,
                })
            sheets.append({
                "title": worksheet.title,
                "max_row": worksheet.max_row,
                "max_column": worksheet.max_column,
                "merged_ranges": [str(item) for item in worksheet.merged_cells.ranges],
                "columns": columns,
            })
        return {"sheets": sheets, "sheet_count": len(sheets), "has_formula": has_formula}

    @staticmethod
    def _infer_type(values: list, formula: str | None) -> str:
        if formula:
            return "formula"
        if any(isinstance(value, bool) for value in values):
            return "text"
        if any(hasattr(value, "year") and hasattr(value, "month") for value in values):
            return "date"
        if values and all(isinstance(value, (int, float)) for value in values):
            return "number"
        return "text"


def ensure_xlsx(filename: str) -> None:
    if Path(filename).suffix.lower() != ".xlsx":
        raise ValueError("仅支持 .xlsx 文件")
