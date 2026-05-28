import os
import sys
import datetime

# Windows 控制台 UTF-8 支持
os.system("chcp 65001 >nul 2>&1")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from core.utils import format_size, is_admin
from core.cleaner import clean_items
from scanner import temp, recycle, browser, windows_update, logs, hibernate, large_files, duplicates


# 菜单项定义：(名称, 扫描函数, 是否特殊清理)
MENU_ITEMS = [
    ("临时文件", temp.scan, None),
    ("回收站", recycle.scan, "recycle_bin"),
    ("浏览器缓存", browser.scan, None),
    ("Windows Update 缓存", windows_update.scan, None),
    ("日志和转储文件", logs.scan, None),
    ("休眠文件", hibernate.scan, "hibernate"),
    ("大文件扫描 (>100MB)", lambda: large_files.scan(min_size_mb=100), None),
    ("重复文件检测 (>1MB)", lambda: duplicates.scan(min_size_kb=1024), None),
]


def print_banner():
    print()
    print("=" * 40)
    print("       C 盘 清 理 工 具")
    print("=" * 40)
    if is_admin():
        print("  [管理员模式]")
    else:
        print("  [普通模式] 部分功能需要管理员权限")
    print()


def print_menu():
    print("请选择操作:")
    print("  1. 扫描全部")
    for i, (name, _, _) in enumerate(MENU_ITEMS, 2):
        print(f"  {i}. {name}")
    print("  0. 退出")
    print()


def scan_category(name: str, scan_func) -> list[dict]:
    """执行单个类别的扫描，显示进度"""
    print(f"  扫描 {name}...", end=" ", flush=True)
    try:
        items = scan_func()
    except Exception as e:
        print(f"出错: {e}")
        return []
    total_size = sum(item.get("size", 0) for item in items)
    if items:
        print(f"发现 {len(items)} 项，共 {format_size(total_size)}")
    else:
        print("无内容")
    return items


def display_results(results: dict[str, list[dict]]):
    """展示扫描结果汇总"""
    print()
    print("-" * 50)

    all_items = []
    grand_total = 0

    for name, items in results.items():
        if not items:
            continue
        total_size = sum(item.get("size", 0) for item in items)
        count = len(items)
        grand_total += total_size
        all_items.extend(items)

        # 特殊项目的额外信息
        extra = ""
        if items and items[0].get("special") == "recycle_bin":
            extra = f' ({items[0].get("item_count", "?")} 项)'
        if items and items[0].get("special") == "hibernate":
            extra = " (需管理员权限)"

        print(f"  {name:<24} {format_size(total_size):>10}  {count} 个文件{extra}")

    print("-" * 50)
    print(f"  {'合计':<24} {format_size(grand_total):>10}")
    print()

    return all_items


def confirm_clean() -> bool:
    """确认是否清理"""
    while True:
        choice = input("确认清理? (y/n): ").strip().lower()
        if choice in ("y", "yes", "是"):
            return True
        if choice in ("n", "no", "否"):
            return False


def execute_clean(results: dict[str, list[dict]]):
    """执行清理"""
    print()
    total_success = total_fail = total_freed = 0

    for name, items in results.items():
        if not items:
            continue

        # 特殊处理回收站
        if items[0].get("special") == "recycle_bin":
            print(f"  清理 {name}...", end=" ", flush=True)
            s, f, freed = recycle.clean_recycle_bin()
            total_success += s
            total_fail += f
            total_freed += freed
            print("完成" if s else "失败")
            continue

        # 特殊处理休眠文件
        if items[0].get("special") == "hibernate":
            print(f"  关闭休眠...", end=" ", flush=True)
            ok, msg = hibernate.disable_hibernate()
            if ok:
                total_success += 1
                total_freed += items[0].get("size", 0)
                print(f"完成 ({format_size(items[0].get('size', 0))})")
            else:
                total_fail += 1
                print(f"失败: {msg}")
            continue

        # 普通文件清理
        print(f"  清理 {name}...", end=" ", flush=True)
        s, f, freed = clean_items(items, name)
        total_success += s
        total_fail += f
        total_freed += freed
        print(f"完成 ({format_size(freed)})")

    print()
    print("=" * 40)
    print(f"  清理完成!")
    print(f"  成功: {total_success} 个文件")
    if total_fail:
        print(f"  失败: {total_fail} 个文件 (可能被占用)")
    print(f"  释放空间: {format_size(total_freed)}")
    print("=" * 40)
    print()


def run_scan_all():
    """扫描全部类别"""
    print("正在扫描...")
    print()
    results = {}
    for name, scan_func, _ in MENU_ITEMS:
        items = scan_category(name, scan_func)
        results[name] = items

    all_items = display_results(results)

    if not all_items:
        print("没有发现可清理的内容。")
        return

    if confirm_clean():
        execute_clean(results)


def run_scan_single(index: int):
    """扫描单个类别"""
    name, scan_func, _ = MENU_ITEMS[index]
    print()
    items = scan_category(name, scan_func)

    if not items:
        print("没有发现可清理的内容。")
        return

    results = {name: items}
    display_results(results)

    if confirm_clean():
        execute_clean(results)


def main():
    print_banner()

    while True:
        print_menu()
        try:
            choice = input("请选择: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if choice == "0":
            print("再见!")
            break
        elif choice == "1":
            run_scan_all()
        elif choice.isdigit() and 2 <= int(choice) <= len(MENU_ITEMS) + 1:
            run_scan_single(int(choice) - 2)
        else:
            print("无效选择，请重新输入。\n")


if __name__ == "__main__":
    main()
