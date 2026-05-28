import os


CATEGORY = "大文件"

# 扫描的根目录
SCAN_ROOTS = [
    os.environ.get("USERPROFILE", ""),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp"),
]

# 跳过的目录（系统关键目录）
SKIP_DIRS = {
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData", "$Recycle.Bin", "System Volume Information",
}


def scan(min_size_mb: int = 100, max_results: int = 50) -> list[dict]:
    """扫描大文件，默认 >100MB，返回 top N"""
    min_size = min_size_mb * 1024 * 1024
    results = []

    for root in SCAN_ROOTS:
        if not root or not os.path.isdir(root):
            continue
        _walk(root, min_size, results)

    # 按大小降序排列，取 top N
    results.sort(key=lambda x: x["size"], reverse=True)
    return results[:max_results]


def _walk(dir_path: str, min_size: int, results: list[dict]):
    """递归遍历查找大文件"""
    try:
        for entry in os.scandir(dir_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    size = entry.stat(follow_symlinks=False).st_size
                    if size >= min_size:
                        results.append({
                            "path": entry.path,
                            "size": size,
                            "category": CATEGORY,
                        })
                elif entry.is_dir(follow_symlinks=False):
                    if entry.name not in SKIP_DIRS and not entry.name.startswith("."):
                        _walk(entry.path, min_size, results)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
