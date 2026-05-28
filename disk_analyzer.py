"""
磁盘深度分析工具
用法: python disk_analyzer.py [盘符]
示例: python disk_analyzer.py C:
"""

import os
import sys
import ctypes

sys.stdout.reconfigure(encoding="utf-8")
os.system("chcp 65001 >nul 2>&1")

from core.utils import format_size, get_dir_size


def get_disk_info(drive: str) -> tuple[int, int, int]:
    """返回 (total, used, free)"""
    free = ctypes.c_ulonglong(0)
    total = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(drive, None, ctypes.byref(total), ctypes.byref(free))
    used = total.value - free.value
    return total.value, used, free.value


def scan_dirs(base: str, top_n: int = 10) -> list[tuple[str, int]]:
    """扫描目录下各子目录大小，返回排序结果"""
    dirs = []
    try:
        for entry in os.scandir(base):
            if entry.is_dir(follow_symlinks=False):
                try:
                    size = get_dir_size(entry.path)
                    dirs.append((entry.name, size))
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    dirs.sort(key=lambda x: x[1], reverse=True)
    return dirs[:top_n]


def scan_large_files(base: str, min_mb: int = 500, top_n: int = 20) -> list[tuple[str, int]]:
    """扫描大文件"""
    min_size = min_mb * 1024 * 1024
    files = []
    skip = {"Windows", "Program Files", "Program Files (x86)", "ProgramData", "$Recycle.Bin"}

    def _walk(d):
        try:
            for e in os.scandir(d):
                try:
                    if e.is_file(follow_symlinks=False):
                        sz = e.stat(follow_symlinks=False).st_size
                        if sz >= min_size:
                            files.append((e.path, sz))
                    elif e.is_dir(follow_symlinks=False):
                        if e.name not in skip and not e.name.startswith("."):
                            _walk(e.path)
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass

    _walk(base)
    files.sort(key=lambda x: x[1], reverse=True)
    return files[:top_n]


def print_section(title: str):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def main():
    drive = sys.argv[1] if len(sys.argv) > 1 else "C:/"

    # 1. 磁盘总览
    print_section("磁盘总览")
    total, used, free = get_disk_info(drive)
    print(f"  总计: {format_size(total)}")
    print(f"  已用: {format_size(used)}")
    print(f"  剩余: {format_size(free)}")

    # 2. 根目录扫描
    print_section(f"{drive} 根目录占用 TOP 10")
    for name, size in scan_dirs(drive, 10):
        print(f"  {format_size(size):>12}  {name}")

    # 3. 用户目录
    user_home = os.path.expanduser("~")
    print_section(f"用户目录 ({user_home}) TOP 10")
    for name, size in scan_dirs(user_home, 10):
        print(f"  {format_size(size):>12}  {name}")

    # 4. AppData 分层
    appdata = os.path.join(user_home, "AppData")
    for sub in ["Local", "Roaming"]:
        subpath = os.path.join(appdata, sub)
        if os.path.isdir(subpath):
            print_section(f"AppData/{sub}")
            for name, size in scan_dirs(subpath, 8):
                print(f"  {format_size(size):>12}  {name}")

    # 5. 已知清理目标
    print_section("已知清理目标")
    targets = [
        (".cache/huggingface", "HF 模型缓存，可重下"),
        (".cache/torch", "PyTorch 缓存"),
        (".conda/envs", "Conda 环境"),
        (".conda/pkgs", "Conda 包缓存"),
        ("AppData/Local/uv", "uv 包缓存"),
        ("AppData/Local/Yarn", "Yarn 缓存"),
        ("AppData/Local/npm", "npm 缓存"),
        ("AppData/Local/pip", "pip 缓存"),
    ]
    for rel_path, desc in targets:
        full = os.path.join(user_home, rel_path.replace("/", os.sep))
        if os.path.isdir(full):
            size = get_dir_size(full)
            if size > 100 * 1024 * 1024:
                print(f"  {format_size(size):>12}  {rel_path}  ({desc})")

    # 6. 大文件扫描
    print_section(f"大文件扫描 (>{500}MB) TOP 20")
    for path, size in scan_large_files(user_home, 500, 20):
        print(f"  {format_size(size):>12}  {path}")

    print()


if __name__ == "__main__":
    main()
