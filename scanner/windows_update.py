import os
from core.utils import get_dir_size, is_admin


CATEGORY = "Windows Update 缓存"

UPDATE_DIRS = [
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "SoftwareDistribution", "Download"),
]


def scan() -> list[dict]:
    """扫描 Update 下载缓存。无管理员权限时只报告大小，不枚举文件。"""
    results = []
    admin = is_admin()
    for update_dir in UPDATE_DIRS:
        if not os.path.isdir(update_dir):
            continue
        size = get_dir_size(update_dir)
        if size <= 0:
            continue
        results.append({
            "path": update_dir,
            "size": size,
            "category": CATEGORY,
            "special": "windows_update",
            "need_admin": not admin,
        })
    return results
