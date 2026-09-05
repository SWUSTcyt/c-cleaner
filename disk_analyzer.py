"""
磁盘深度分析工具
用法:
  python disk_analyzer.py              分析系统盘（C）
  python disk_analyzer.py --others     分析其他数据盘（自动发现）
  python disk_analyzer.py E:           只分析指定盘（调试用）
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.system("chcp 65001 >nul 2>&1")

from core.utils import format_size, get_dir_size
from core.drives import data_drives, format_drive_list, normalize_root, system_drive
from scanner.data_disk import (
    flatten_reports,
    print_drive_overview,
    print_tier_section,
    scan_data_drives,
    scan_drive,
)


def get_disk_info(drive: str) -> tuple[int, int, int]:
    """返回 (total, used, free)"""
    import ctypes

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
    """扫描大文件。保留 .cache / .conda / .lmstudio 等点目录。"""
    min_size = min_mb * 1024 * 1024
    files = []
    skip = {
        "Windows", "Program Files", "Program Files (x86)", "ProgramData",
        "$Recycle.Bin", "System Volume Information", ".git", "node_modules",
    }

    def _walk(d):
        try:
            for e in os.scandir(d):
                try:
                    if e.is_file(follow_symlinks=False):
                        sz = e.stat(follow_symlinks=False).st_size
                        if sz >= min_size:
                            files.append((e.path, sz))
                    elif e.is_dir(follow_symlinks=False):
                        if e.name not in skip:
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


def print_disk_overview(drive: str):
    print_section("磁盘总览")
    total, used, free = get_disk_info(drive)
    print(f"  盘符: {drive.rstrip(os.sep)}")
    print(f"  总计: {format_size(total)}")
    print(f"  已用: {format_size(used)}")
    print(f"  剩余: {format_size(free)}")


def analyze_system_drive():
    drive = system_drive()
    print_disk_overview(drive)

    print_section(f"{drive} 根目录占用 TOP 10")
    for name, size in scan_dirs(drive, 10):
        print(f"  {format_size(size):>12}  {name}")

    user_home = os.path.expanduser("~")
    print_section(f"用户目录 ({user_home}) TOP 10")
    for name, size in scan_dirs(user_home, 10):
        print(f"  {format_size(size):>12}  {name}")

    appdata = os.path.join(user_home, "AppData")
    for sub in ["Local", "Roaming"]:
        subpath = os.path.join(appdata, sub)
        if os.path.isdir(subpath):
            print_section(f"AppData/{sub}")
            for name, size in scan_dirs(subpath, 8):
                print(f"  {format_size(size):>12}  {name}")

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
    found = False
    for rel_path, desc in targets:
        full = os.path.join(user_home, rel_path.replace("/", os.sep))
        if os.path.isdir(full):
            size = get_dir_size(full)
            if size > 100 * 1024 * 1024:
                found = True
                print(f"  {format_size(size):>12}  {rel_path}  ({desc})")
    if not found:
        print("  （无超过 100MB 的已知缓存）")

    print_section("大文件扫描 (>500MB) TOP 20")
    for path, size in scan_large_files(user_home, 500, 20):
        print(f"  {format_size(size):>12}  {path}")

    print()


def _print_data_reports(reports: list[dict]):
    if not reports:
        print("没有可分析的数据盘。")
        return

    for report in reports:
        print_disk_overview(report["root"])
        print_drive_overview(report)

    safe = flatten_reports(reports, "safe")
    confirm = flatten_reports(reports, "confirm")
    keep = flatten_reports(reports, "keep")

    print_section("分类报告")
    print_tier_section("【可安全清理】", safe)
    print_tier_section("【需要确认】", confirm)
    print_tier_section("【建议保留】", keep, limit=8)
    print()
    print(f"  可安全清理 {format_size(sum(i['size'] for i in safe))}")
    print(f"  需要确认   {format_size(sum(i['size'] for i in confirm))}")
    print()


def analyze_data_drives():
    roots = data_drives()
    print_section("数据盘")
    print(f"  自动发现: {format_drive_list(roots)}")
    print("  （按目录统计大小，盘较大时可能需要几分钟）")
    _print_data_reports(scan_data_drives(roots))


def analyze_one_drive(drive: str):
    root = normalize_root(drive)
    if root.upper() == system_drive().upper():
        analyze_system_drive()
        return
    print_section("指定数据盘")
    print(f"  目标: {root.rstrip(os.sep)}")
    _print_data_reports([scan_drive(root)])


def main():
    args = [a for a in sys.argv[1:] if a]
    if not args:
        analyze_system_drive()
    elif args[0] in ("--others", "-o", "其他"):
        analyze_data_drives()
    else:
        analyze_one_drive(args[0])


if __name__ == "__main__":
    main()
