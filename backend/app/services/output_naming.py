import re


def final_output_name(task_id: int, batch_id: str | None, notice_config: dict[str, str]) -> str:
    title = notice_config.get("title") or "Excel通报"
    as_of_date = notice_config.get("as_of_date") or "未定日期"
    safe_title = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", title).strip("_")[:40] or "Excel通报"
    safe_date = re.sub(r"[^0-9A-Za-z_-]+", "-", as_of_date).strip("-")[:20] or "未定日期"
    batch_suffix = (batch_id or "single")[:8]
    return f"{safe_title}_{safe_date}_{batch_suffix}_task{task_id}.xlsx"
