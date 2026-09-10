import os
import sys

# Windows 控制台 UTF-8 支持
os.system("chcp 65001 >nul 2>&1")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from core.utils import format_size, is_admin
from core.cleaner import clean_items, log_summary, wipe_dir_contents
from core.drives import data_drives, format_drive_list, system_drive
from scanner import temp, recycle, browser, windows_update, logs, hibernate, large_files, duplicates, caches
from scanner.data_disk import (
    KIND_LABEL,
    flatten_reports,
    group_by_kind,
    print_drive_overview,
    print_tier_section,
    scan_data_drives,
)


# C 盘可随「扫描 C 盘」一起确认清理的项目（不含大文件/重复文件/休眠）
C_JUNK_ITEMS = [
    ("临时文件", temp.scan),
    ("回收站", recycle.scan),
    ("浏览器缓存", browser.scan),
    ("Windows Update 缓存", windows_update.scan),
    ("日志和转储文件", logs.scan),
    ("已知缓存", caches.scan),
]

C_EXTRA_ITEMS = [
    ("休眠文件", hibernate.scan),
    ("大文件扫描 (>100MB)", lambda: large_files.scan(min_size_mb=100)),
    ("重复文件检测 (>1MB)", lambda: duplicates.scan(min_size_kb=1024)),
]

C_MENU_ITEMS = C_JUNK_ITEMS + C_EXTRA_ITEMS


def print_banner():
    print()
    print("=" * 44)
    print("       磁 盘 清 理 工 具")
    print("=" * 44)
    sys_label = system_drive().rstrip("\\")
    print(f"  系统盘: {sys_label}")
    others = data_drives()
    print(f"  数据盘: {format_drive_list(others)}")
    if is_admin():
        print("  [管理员模式]")
    else:
        print("  [普通模式] C 盘部分功能需要管理员权限")
    print()


def print_menu():
    others = format_drive_list(data_drives())
    print("请选择操作:")
    print("  1. 扫描 C 盘（系统垃圾 + 已知缓存）")
    print(f"  2. 扫描其他盘（数据盘: {others}）")
    print("  3. 扫描全部")
    print("  ---------- C 盘单项 ----------")
    for i, (name, _) in enumerate(C_JUNK_ITEMS, 4):
        print(f"  {i}. {name}")
    extra_start = 4 + len(C_JUNK_ITEMS)
    print("  ---------- 需单独确认 ----------")
    for i, (name, _) in enumerate(C_EXTRA_ITEMS, extra_start):
        print(f"  {i}. {name}")
    print("  0. 退出")
    print()


def ask_yes_no(prompt: str) -> bool:
    while True:
        try:
            choice = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if choice in ("y", "yes", "是"):
            return True
        if choice in ("n", "no", "否", ""):
            return False


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


def display_c_results(results: dict[str, list[dict]]):
    """展示 C 盘扫描结果汇总"""
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

        extra = ""
        if items and items[0].get("special") == "recycle_bin":
            extra = f' ({items[0].get("item_count", "?")} 项)'
        if items and items[0].get("special") == "hibernate":
            extra = " (需管理员权限)"
        if items and items[0].get("need_admin"):
            extra = " (需管理员，将跳过)"
        if name == "已知缓存":
            extra = f"  目录"

        print(f"  {name:<24} {format_size(total_size):>10}  {count} 个文件{extra}")
        if name == "已知缓存":
            for item in items[:8]:
                reason = item.get("reason", "")
                print(f"      {format_size(item['size']):>10}  {reason}")
            if len(items) > 8:
                print(f"      ... 其余 {len(items) - 8} 项")

    print("-" * 50)
    print(f"  {'合计':<24} {format_size(grand_total):>10}")
    print()

    return all_items


def execute_clean(results: dict[str, list[dict]]):
    """执行 C 盘清理"""
    print()
    total_success = total_fail = total_freed = 0

    for name, items in results.items():
        if not items:
            continue

        if items[0].get("special") == "recycle_bin":
            print(f"  清理 {name}...", end=" ", flush=True)
            s, f, freed = recycle.clean_recycle_bin()
            total_success += s
            total_fail += f
            total_freed += freed
            print("完成" if s else "失败")
            continue

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

        if items[0].get("special") == "windows_update":
            print(f"  清理 {name}...", end=" ", flush=True)
            if items[0].get("need_admin"):
                print("跳过（需要管理员权限）")
                continue
            s = f = freed = 0
            for item in items:
                cs, cf, cfree = wipe_dir_contents(item["path"])
                s += cs
                f += cf
                freed += cfree
            log_summary(name, s, f, freed)
            total_success += s
            total_fail += f
            total_freed += freed
            print(f"完成 ({format_size(freed)})")
            continue

        print(f"  清理 {name}...", end=" ", flush=True)
        s, f, freed = clean_items(items, name)
        total_success += s
        total_fail += f
        total_freed += freed
        print(f"完成 ({format_size(freed)})")

    print()
    print("=" * 44)
    print("  清理完成!")
    print(f"  成功: {total_success} 个文件")
    if total_fail:
        print(f"  失败: {total_fail} 个文件 (可能被占用)")
    print(f"  释放空间: {format_size(total_freed)}")
    print("=" * 44)
    print()


def run_scan_c_all():
    """扫描 C 盘全部系统垃圾"""
    print()
    sys_label = system_drive().rstrip("\\")
    print(f"正在扫描系统盘 {sys_label} （系统垃圾 + 已知缓存）...")
    print()
    results = {}
    for name, scan_func in C_JUNK_ITEMS:
        items = scan_category(name, scan_func)
        results[name] = items

    all_items = display_c_results(results)

    if not all_items:
        print("没有发现可清理的内容。")
        return

    if ask_yes_no("确认清理以上 C 盘项目? (y/n): "):
        execute_clean(results)


def run_scan_c_single(index: int):
    """扫描 C 盘单个类别"""
    name, scan_func = C_MENU_ITEMS[index]
    print()
    items = scan_category(name, scan_func)

    if not items:
        print("没有发现可清理的内容。")
        return

    results = {name: items}
    display_c_results(results)

    if ask_yes_no("确认清理? (y/n): "):
        execute_clean(results)


def _clean_data_items(items: list[dict], title: str):
    if not items:
        return
    print()
    print(f"  清理{title}...", end=" ", flush=True)
    s, f, freed = clean_items(items, title)
    print(f"完成 ({format_size(freed)})")
    if f:
        print(f"  其中 {f} 项失败（可能被占用）")


def _pick_confirm_groups(items: list[dict]) -> list[dict]:
    """按类别勾选需要确认的项。"""
    groups = group_by_kind(items)
    if not groups:
        return []

    print()
    print("  【需要确认】按类选择（逗号分隔编号，all=全部，回车跳过）:")
    for i, (kind, group, total) in enumerate(groups, 1):
        label = KIND_LABEL.get(kind, kind)
        print(f"    {i}. {label:<12} {len(group)} 项  {format_size(total)}")
        for item in group[:3]:
            print(f"         {format_size(item['size']):>10}  {item['path']}")
        if len(group) > 3:
            print(f"         ... 其余 {len(group) - 3} 项")

    try:
        raw = input("  选择: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return []

    if not raw:
        return []
    if raw in ("all", "a", "全部"):
        return items

    chosen: list[dict] = []
    for part in raw.replace("，", ",").split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        idx = int(part) - 1
        if 0 <= idx < len(groups):
            chosen.extend(groups[idx][1])
    return chosen


def run_scan_data_disks():
    """扫描除系统盘外的固定硬盘。"""
    roots = data_drives()
    if not roots:
        print("未发现其他固定磁盘。")
        return

    print()
    print(f"正在扫描数据盘 {format_drive_list(roots)} ...")
    print("（按目录统计大小，盘较大时可能需要几分钟）")
    print()

    reports = scan_data_drives(roots)
    if not reports:
        print("没有可扫描的数据盘。")
        return

    for report in reports:
        print_drive_overview(report)

    safe = flatten_reports(reports, "safe")
    confirm = flatten_reports(reports, "confirm")
    keep = flatten_reports(reports, "keep")

    print()
    print("-" * 50)
    print_tier_section("【可安全清理】", safe)
    print_tier_section("【需要确认】", confirm)
    print_tier_section("【建议保留】", keep, limit=8)
    print()
    print("-" * 50)
    print(f"  可安全清理 {format_size(sum(i['size'] for i in safe))}")
    print(f"  需要确认   {format_size(sum(i['size'] for i in confirm))}")
    print("  建议保留项不会进入清理。")
    print()

    if not safe and not confirm:
        print("没有发现可清理项（大头都在建议保留里）。")
        return

    if safe and ask_yes_no("清理「可安全清理」? (y/n): "):
        _clean_data_items(safe, "数据盘-可安全清理")

    if confirm:
        selected = _pick_confirm_groups(confirm)
        if selected:
            print()
            total = sum(i["size"] for i in selected)
            print(f"  已选 {len(selected)} 项，共 {format_size(total)}")
            if ask_yes_no("确认删除以上需要确认的项? (y/n): "):
                _clean_data_items(selected, "数据盘-需要确认")


def run_scan_all():
    """先 C 盘，再数据盘，分两次确认。"""
    run_scan_c_all()
    print()
    print("=" * 44)
    print("  接下来扫描其他数据盘")
    print("=" * 44)
    run_scan_data_disks()


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
            run_scan_c_all()
        elif choice == "2":
            run_scan_data_disks()
        elif choice == "3":
            run_scan_all()
        elif choice.isdigit() and 4 <= int(choice) <= len(C_MENU_ITEMS) + 3:
            run_scan_c_single(int(choice) - 4)
        else:
            print("无效选择，请重新输入。\n")


if __name__ == "__main__":
    main()
