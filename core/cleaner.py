import os
import json
import shutil
import datetime
from core.utils import safe_delete


LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cleanup_log.json")


def load_log() -> list[dict]:
    """加载清理日志"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_log(entries: list[dict]):
    """保存清理日志"""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def clean_items(items: list[dict], category: str) -> tuple[int, int, int]:
    """
    清理指定条目列表。
    items: [{"path": str, "size": int}, ...]
    返回: (成功删除数, 失败数, 释放字节数)
    """
    log_entries = load_log()
    now = datetime.datetime.now().isoformat()
    success_count = fail_count = freed_bytes = 0

    for item in items:
        path = item["path"]
        size = item.get("size", 0)

        deleted = False
        if os.path.isfile(path):
            deleted = safe_delete(path)
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
                deleted = True
            except (PermissionError, OSError):
                deleted = False

        if deleted:
            success_count += 1
            freed_bytes += size
            log_entries.append({
                "time": now,
                "category": category,
                "path": path,
                "size": size,
            })
        else:
            fail_count += 1

    save_log(log_entries)
    return success_count, fail_count, freed_bytes
