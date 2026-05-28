import os
from core.utils import scan_dir_files


TEMP_DIRS = [
    os.environ.get("TEMP", ""),
    os.environ.get("TMP", ""),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp"),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Prefetch"),
]

CATEGORY = "临时文件"


def scan() -> list[dict]:
    """扫描系统临时文件"""
    results = []
    for temp_dir in TEMP_DIRS:
        if not temp_dir or not os.path.isdir(temp_dir):
            continue
        for file_path in scan_dir_files(temp_dir):
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
