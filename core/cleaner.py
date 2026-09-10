import os
import json
import datetime
from core.utils import get_dir_size, safe_delete, _clear_readonly, _rmtree_readonly


LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cleanup_log.json")
MAX_LOG_ENTRIES = 100
MAX_FAIL_SAMPLES = 5


def load_log() -> list[dict]:
    """加载清理日志。旧版按文件记账的记录会丢弃，避免膨胀和写入用户路径。"""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    if not isinstance(data, list):
        return []
    if data and isinstance(data[0], dict) and "success" not in data[0]:
        return []
    return data


def save_log(entries: list[dict]):
    """保存清理日志（只保留最近若干条汇总）。"""
    trimmed = entries[-MAX_LOG_ENTRIES:]
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def wipe_dir_contents(dir_path: str) -> tuple[int, int, int]:
    """删除目录内条目，保留目录本身。返回 (成功, 失败, 估算释放字节)。"""
    success = fail = freed = 0
    try:
        names = os.listdir(dir_path)
    except (PermissionError, OSError):
        return 0, 1, 0
    for name in names:
        child = os.path.join(dir_path, name)
        try:
            if os.path.isdir(child) and not os.path.islink(child):
                size = 0
                try:
                    size = get_dir_size(child)
                except OSError:
                    pass
                _rmtree_readonly(child)
                success += 1
                freed += size
            else:
                size = os.path.getsize(child) if os.path.isfile(child) else 0
                try:
                    os.remove(child)
                except PermissionError:
                    _clear_readonly(child)
                    os.remove(child)
                success += 1
                freed += size
        except (PermissionError, OSError):
            fail += 1
    return success, fail, freed


def clean_items(items: list[dict], category: str) -> tuple[int, int, int]:
    """
    清理指定条目列表。
    items: [{"path": str, "size": int}, ...]
    返回: (成功删除数, 失败数, 释放字节数)
    """
    now = datetime.datetime.now().isoformat()
    success_count = fail_count = freed_bytes = 0
    failed_samples: list[str] = []

    for item in items:
        path = item["path"]
        size = item.get("size", 0)

        deleted = False
        if os.path.isfile(path):
            deleted = safe_delete(path)
        elif os.path.isdir(path):
            try:
                _rmtree_readonly(path)
                deleted = True
            except (PermissionError, OSError):
                deleted = False

        if deleted:
            success_count += 1
            freed_bytes += size
        else:
            fail_count += 1
            if len(failed_samples) < MAX_FAIL_SAMPLES:
                failed_samples.append(path)

    log_entries = load_log()
    log_entries.append({
        "time": now,
        "category": category,
        "success": success_count,
        "fail": fail_count,
        "freed": freed_bytes,
        "failed_samples": failed_samples,
    })
    save_log(log_entries)
    return success_count, fail_count, freed_bytes


def log_summary(category: str, success: int, fail: int, freed: int, failed_samples: list[str] | None = None):
    """写入一条汇总日志。"""
    log_entries = load_log()
    log_entries.append({
        "time": datetime.datetime.now().isoformat(),
        "category": category,
        "success": success,
        "fail": fail,
        "freed": freed,
        "failed_samples": failed_samples or [],
    })
    save_log(log_entries)
