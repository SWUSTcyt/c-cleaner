import os
from core.utils import scan_dir_files


CATEGORY = "Windows Update 缓存"

UPDATE_DIRS = [
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "SoftwareDistribution", "Download"),
]


def scan() -> list[dict]:
    """扫描 Windows Update 缓存"""
    results = []
    for update_dir in UPDATE_DIRS:
        if not os.path.isdir(update_dir):
            continue
        for file_path in scan_dir_files(update_dir):
            try:
                size = os.path.getsize(file_path)
            except OSError:
                continue
            results.append({
                "path": file_path,
                "size": size,
                "category": CATEGORY,
            })
    return results
