import os
from core.utils import scan_dir_files


CATEGORY = "日志和转储文件"

LOG_DIRS = [
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Logs"),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "debug"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER"),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Minidump"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "CrashDumps"),
]

LOG_EXTENSIONS = [".log", ".dmp", ".wer", ".tmp", ".bak"]


def scan() -> list[dict]:
    """扫描日志文件和错误转储"""
    results = []
    for log_dir in LOG_DIRS:
        if not log_dir or not os.path.isdir(log_dir):
            continue
        for file_path in scan_dir_files(log_dir, LOG_EXTENSIONS):
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
