import os
import hashlib
from collections import defaultdict


CATEGORY = "重复文件"

SCAN_ROOTS = [
    os.environ.get("USERPROFILE", ""),
]

SKIP_DIRS = {
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData", "$Recycle.Bin", "System Volume Information",
    ".git", "node_modules", "__pycache__",
}


def _file_hash(file_path: str, chunk_size: int = 65536) -> str | None:
    """计算文件 MD5 哈希"""
    try:
        h = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError, IOError):
        return None


def scan(max_results: int = 100, min_size_kb: int = 1024) -> list[dict]:
    """
    扫描重复文件。
    先按大小分组（快速排除不同大小的文件），再对相同大小的文件做哈希比对。
    返回除第一个原始文件外的重复文件列表。
    """
    min_size = min_size_kb * 1024

    # 第一步：按大小收集文件
    size_groups: dict[int, list[str]] = defaultdict(list)
    for root in SCAN_ROOTS:
        if not root or not os.path.isdir(root):
            continue
        _collect_by_size(root, min_size, size_groups)

    # 第二步：对相同大小的文件做哈希比对
    duplicates = []
    for size, files in size_groups.items():
        if len(files) < 2:
            continue
        hash_groups: dict[str, list[str]] = defaultdict(list)
        for f in files:
            h = _file_hash(f)
            if h:
                hash_groups[h].append(f)

        for hash_val, hash_files in hash_groups.items():
            if len(hash_files) < 2:
                continue
            # 保留第一个，其余标记为重复
            for dup_path in hash_files[1:]:
                duplicates.append({
                    "path": dup_path,
                    "size": size,
                    "category": CATEGORY,
                    "original": hash_files[0],
                })

    duplicates.sort(key=lambda x: x["size"], reverse=True)
    return duplicates[:max_results]


def _collect_by_size(dir_path: str, min_size: int, size_groups: dict[int, list[str]]):
    """递归按文件大小分组"""
    try:
        for entry in os.scandir(dir_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    size = entry.stat(follow_symlinks=False).st_size
                    if size >= min_size:
                        size_groups[size].append(entry.path)
                elif entry.is_dir(follow_symlinks=False):
                    if entry.name not in SKIP_DIRS and entry.name != ".git":
                        _collect_by_size(entry.path, min_size, size_groups)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
