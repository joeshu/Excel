import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RecalculationResult:
    engine: str
    recalculated: bool
    message: str


def recalculate(path: str) -> RecalculationResult:
    file_path = Path(path)
    if sys.platform == "win32":
        result = _recalculate_with_excel(file_path)
        if result.recalculated:
            return result
    libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
    if libreoffice:
        result = _recalculate_with_libreoffice(libreoffice, file_path)
        if result.recalculated:
            return result
    return RecalculationResult("formula_only", False, "未检测到 Excel 或 LibreOffice，文件将由 Excel 打开时重新计算")


def _recalculate_with_excel(path: Path) -> RecalculationResult:
    try:
        import win32com.client
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        workbook = excel.Workbooks.Open(str(path.resolve()), UpdateLinks=0, ReadOnly=False)
        workbook.RefreshAll()
        excel.CalculateFullRebuild()
        workbook.Save()
        workbook.Close(SaveChanges=True)
        excel.Quit()
        return RecalculationResult("excel", True, "已使用 Microsoft Excel COM 完成重算")
    except Exception as error:
        return RecalculationResult("excel", False, f"Excel COM 重算失败: {error}")


def _recalculate_with_libreoffice(command: str, path: Path) -> RecalculationResult:
    try:
        with tempfile.TemporaryDirectory() as directory:
            temporary_path = Path(directory) / "recalculation_input.xlsx"
            shutil.copyfile(path, temporary_path)
            result = subprocess.run(
                [command, "--headless", "--convert-to", "xlsx", "--outdir", directory, str(temporary_path)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            recalculated = Path(directory) / temporary_path.name
            if result.returncode == 0 and recalculated.is_file():
                shutil.copyfile(recalculated, path)
                return RecalculationResult("libreoffice", True, "已使用 LibreOffice 完成重算")
            return RecalculationResult("libreoffice", False, result.stderr.strip() or "LibreOffice 重算失败")
    except Exception as error:
        return RecalculationResult("libreoffice", False, f"LibreOffice 重算失败: {error}")
