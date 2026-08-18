from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook


def build_batch_summary(tasks, output_path: str) -> str:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "批次汇总"
    sheet.append(["任务 ID", "数据源 ID", "状态", "输出文件", "SHA-256"])
    for task in tasks:
        sheet.append([task.id, task.data_source_id, task.status, Path(task.output_path).name if task.output_path else "", task.output_sha256 or ""])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return output_path


def build_batch_zip(tasks, archive_path: str, summary_path: str) -> str:
    build_batch_summary(tasks, summary_path)
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(summary_path, arcname="批次汇总.xlsx")
        for task in tasks:
            if task.output_path and Path(task.output_path).is_file():
                archive.write(task.output_path, arcname=Path(task.output_path).name)
    return archive_path
