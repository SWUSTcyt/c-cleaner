"""数据盘扫描：旧版本、更新缓存、压缩包重复、模型/Docker/微信等。"""

import os
import re
from collections import defaultdict

from core.utils import format_size


TIER_SAFE = "safe"
TIER_CONFIRM = "confirm"
TIER_KEEP = "keep"

# 全盘递归以得到准确大小，但只把浅层目录记入索引
INDEX_DEPTH = 4

SKIP_DIR_NAMES = {
    "$recycle.bin",
    "system volume information",
    "config.msi",
    "recovery",
    "node_modules",
    ".git",
    "__pycache__",
}

ARCHIVE_EXT = {".zip", ".rar", ".7z"}
INSTALLER_EXT = {".exe", ".msi"}
VERSION_NAME = re.compile(r"^\d+(\.\d+)+([._-]\d+)*$", re.IGNORECASE)

DOWNLOAD_HINTS = ("download", "downloads", "下载")

MODEL_DIR_NAMES = {
    ".lmstudio",
    "ollama",
    "ollamamodels",
    "huggingface",
    "huggingface-hub",
}


def _is_model_dir(name: str) -> bool:
    n = name.lower()
    if n in MODEL_DIR_NAMES:
        return True
    return n.startswith("ollama")

KIND_LABEL = {
    "update_cache": "软件更新缓存",
    "dup_archive": "已解压的压缩包",
    "old_version": "软件旧版本",
    "old_wechat": "旧版微信目录",
    "qq_chat": "QQ 聊天记录",
    "docker": "Docker 虚拟盘",
    "models": "本地 AI 模型",
    "installer": "下载目录安装包",
    "steam_extra": "Steam 附加工具",
    "steam_game": "Steam 游戏",
    "wechat_current": "当前微信数据",
    "pagefile": "系统虚拟内存",
}


def _item(path: str, size: int, tier: str, kind: str, reason: str) -> dict:
    return {
        "path": path,
        "size": size,
        "category": KIND_LABEL.get(kind, kind),
        "tier": tier,
        "kind": kind,
        "reason": reason,
    }


def _is_version_name(name: str) -> bool:
    return bool(VERSION_NAME.match(name))


def _version_key(name: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", name))


def _is_download_dir(name: str) -> bool:
    lower = name.lower()
    return any(h in lower for h in DOWNLOAD_HINTS)


def _index_drive(root: str, max_depth: int = INDEX_DEPTH) -> tuple[dict[str, int], dict[str, list[str]], list[tuple[str, str, int]]]:
    """一次遍历：浅层目录大小、子目录列表、浅层关注文件。"""
    dir_size: dict[str, int] = {}
    children: dict[str, list[str]] = defaultdict(list)
    files: list[tuple[str, str, int]] = []

    def walk(path: str, depth: int) -> int:
        total = 0
        try:
            entries = list(os.scandir(path))
        except (PermissionError, OSError):
            return 0

        for entry in entries:
            try:
                if entry.is_file(follow_symlinks=False):
                    size = entry.stat(follow_symlinks=False).st_size
                    total += size
                    if depth <= max_depth:
                        ext = os.path.splitext(entry.name)[1].lower()
                        name_l = entry.name.lower()
                        if (
                            ext in ARCHIVE_EXT
                            or ext in INSTALLER_EXT
                            or ext == ".vhdx"
                            or name_l in ("pagefile.sys", "hiberfil.sys")
                        ):
                            files.append((entry.path, entry.name, size))
                elif entry.is_dir(follow_symlinks=False):
                    if entry.name.lower() in SKIP_DIR_NAMES:
                        continue
                    sub = walk(entry.path, depth + 1)
                    total += sub
                    if depth < max_depth:
                        children[path].append(entry.path)
            except (PermissionError, OSError):
                continue

        if depth <= max_depth:
            dir_size[path] = total
        return total

    walk(root, 0)
    return dir_size, children, files


def _dir_name(path: str) -> str:
    return os.path.basename(path.rstrip("\\/")) or path


def _collect_patterns(root: str, dir_size: dict[str, int], children: dict[str, list[str]], files: list[tuple[str, str, int]]) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    def _norm(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    def add(item: dict):
        path = _norm(item["path"])
        if item["size"] <= 0:
            return
        sep = os.sep
        for existing in seen:
            if path == existing:
                return
            if path.startswith(existing + sep) or existing.startswith(path + sep):
                return
        seen.add(path)
        item["path"] = os.path.abspath(item["path"])
        items.append(item)

    child_names: dict[str, set[str]] = {
        parent: {_dir_name(c) for c in kids} for parent, kids in children.items()
    }

    # 压缩包旁已有同名解压目录 → 可安全清理压缩包
    for path, name, size in files:
        stem, ext = os.path.splitext(name)
        if ext.lower() not in ARCHIVE_EXT:
            continue
        parent = os.path.dirname(path)
        if stem in child_names.get(parent, set()):
            add(_item(path, size, TIER_SAFE, "dup_archive", f"同目录已有解压文件夹「{stem}」"))

    # AutoUpdate\Download 更新缓存
    for path, size in dir_size.items():
        parent = os.path.dirname(path)
        if _dir_name(path).lower() == "download" and _dir_name(parent).lower() == "autoupdate":
            add(_item(path, size, TIER_SAFE, "update_cache", "软件自动更新下载缓存"))

    # 同一父目录下多个版本号文件夹，只留最新
    for parent, kids in children.items():
        version_dirs = [p for p in kids if _is_version_name(_dir_name(p))]
        if len(version_dirs) < 2:
            continue
        version_dirs.sort(key=lambda p: _version_key(_dir_name(p)))
        newest = _dir_name(version_dirs[-1])
        for old in version_dirs[:-1]:
            add(_item(
                old,
                dir_size.get(old, 0),
                TIER_CONFIRM,
                "old_version",
                f"旧版本，同目录最新为 {newest}（请先退出对应软件）",
            ))

    # 微信：同时存在 4.x 与旧版 WeChat Files
    wechat_new = [p for p in dir_size if _dir_name(p).lower() == "xwechat_files"]
    wechat_old = [p for p in dir_size if _dir_name(p) == "WeChat Files"]
    if wechat_new and wechat_old:
        for p in wechat_old:
            add(_item(p, dir_size.get(p, 0), TIER_CONFIRM, "old_wechat", "旧版微信目录，当前已有微信 4.x 数据"))
        for p in wechat_new:
            add(_item(p, dir_size.get(p, 0), TIER_KEEP, "wechat_current", "当前微信 4.x 聊天数据，默认保留"))
    elif wechat_new:
        for p in wechat_new:
            add(_item(p, dir_size.get(p, 0), TIER_KEEP, "wechat_current", "当前微信 4.x 聊天数据，默认保留"))
    else:
        for p in wechat_old:
            add(_item(p, dir_size.get(p, 0), TIER_KEEP, "wechat_current", "微信聊天数据，默认保留"))

    # QQ 聊天记录（不用 QQ 后可确认删除；请先退出 QQ）
    for path, size in dir_size.items():
        name = _dir_name(path)
        name_l = name.lower()
        if size < 100 * 1024 * 1024:
            continue
        is_qq = (
            name == "Tencent Files"
            or "聊天消息" in name
            or (name_l.startswith("qq_") and "download" not in name_l)
        )
        if is_qq:
            add(_item(path, size, TIER_CONFIRM, "qq_chat", "QQ 本地聊天记录，删除前请先退出 QQ"))

    # Docker 虚拟盘（优先具体目录，避免和父目录、vhdx 重复统计）
    for path, size in dir_size.items():
        if _dir_name(path) == "DockerDesktopWSL" and size >= 512 * 1024 * 1024:
            add(_item(path, size, TIER_CONFIRM, "docker", "Docker 数据，删除后镜像和容器都会丢失"))
    docker_root = os.path.join(root, "docker")
    docker_key = None
    docker_size = 0
    for path, size in dir_size.items():
        if os.path.normcase(path) == os.path.normcase(docker_root):
            docker_key = path
            docker_size = size
            break
    if docker_key and _norm(docker_key) not in seen and docker_size >= 512 * 1024 * 1024:
        add(_item(docker_key, docker_size, TIER_CONFIRM, "docker", "Docker 数据，删除后镜像和容器都会丢失"))

    for path, name, size in files:
        if os.path.splitext(name)[1].lower() == ".vhdx" and size >= 512 * 1024 * 1024:
            add(_item(path, size, TIER_CONFIRM, "docker", "WSL/Docker 虚拟磁盘"))

    # 本地模型
    for path, size in dir_size.items():
        if _is_model_dir(_dir_name(path)) and size >= 100 * 1024 * 1024:
            add(_item(path, size, TIER_CONFIRM, "models", "本地模型文件，删除后需重新下载"))

    # 下载目录里的安装包
    for path, name, size in files:
        ext = os.path.splitext(name)[1].lower()
        if ext not in INSTALLER_EXT or size < 20 * 1024 * 1024:
            continue
        parent_name = _dir_name(os.path.dirname(path))
        if _is_download_dir(parent_name):
            add(_item(path, size, TIER_CONFIRM, "installer", "下载目录中的安装包"))

    # Steam：游戏默认保留，Benchmark/Tool 需确认
    for parent, kids in children.items():
        if _dir_name(parent).lower() != "common":
            continue
        if "steamapps" not in parent.lower():
            continue
        for game in kids:
            name = _dir_name(game)
            size = dir_size.get(game, 0)
            lower = name.lower()
            if "benchmark" in lower or lower.endswith("tool") or " tool" in lower:
                add(_item(game, size, TIER_CONFIRM, "steam_extra", "Steam 附加/跑分工具，游戏本体仍保留"))
            else:
                add(_item(game, size, TIER_KEEP, "steam_game", "Steam 游戏，默认保留"))

    # pagefile / hiberfil
    for path, name, size in files:
        if name.lower() in ("pagefile.sys", "hiberfil.sys"):
            add(_item(path, size, TIER_KEEP, "pagefile", "系统虚拟内存/休眠文件，不要直接删除"))

    return items


def scan_drive(root: str) -> dict:
    """扫描一块数据盘，返回总览 + 三级条目。"""
    print(f"  索引 {root} ...", flush=True)
    dir_size, children, files = _index_drive(root)
    items = _collect_patterns(root, dir_size, children, files)

    top = []
    for child in children.get(root, []):
        top.append((_dir_name(child), dir_size.get(child, 0)))
    # 根目录大文件（pagefile 等）
    root_files = [(name, size) for path, name, size in files if os.path.dirname(path).rstrip("\\") == root.rstrip("\\")]
    for name, size in root_files:
        top.append((name, size))
    top.sort(key=lambda x: x[1], reverse=True)

    grouped = {TIER_SAFE: [], TIER_CONFIRM: [], TIER_KEEP: []}
    for item in items:
        grouped[item["tier"]].append(item)
    for tier in grouped:
        grouped[tier].sort(key=lambda x: x["size"], reverse=True)

    return {
        "root": root,
        "top": top[:12],
        "safe": grouped[TIER_SAFE],
        "confirm": grouped[TIER_CONFIRM],
        "keep": grouped[TIER_KEEP],
    }


def scan_data_drives(roots: list[str] | None = None) -> list[dict]:
    from core.drives import data_drives

    if roots is None:
        roots = data_drives()
    reports = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        reports.append(scan_drive(root))
    return reports


def flatten_reports(reports: list[dict], tier: str) -> list[dict]:
    items = []
    for report in reports:
        items.extend(report.get(tier, []))
    items.sort(key=lambda x: x["size"], reverse=True)
    return items


def group_by_kind(items: list[dict]) -> list[tuple[str, list[dict], int]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        groups[item.get("kind", "other")].append(item)
    result = []
    for kind, group in groups.items():
        total = sum(i["size"] for i in group)
        result.append((kind, group, total))
    result.sort(key=lambda x: x[2], reverse=True)
    return result


def print_drive_overview(report: dict):
    label = report["root"].rstrip("\\")
    print(f"\n  [{label}] 根目录占用")
    for name, size in report["top"]:
        if size <= 0:
            continue
        print(f"    {format_size(size):>10}  {name}")


def print_tier_section(title: str, items: list[dict], limit: int = 12):
    total = sum(i["size"] for i in items)
    print(f"\n  {title}  {len(items)} 项，{format_size(total)}")
    if not items:
        print("    （无）")
        return
    for item in items[:limit]:
        print(f"    {format_size(item['size']):>10}  {item['path']}")
        print(f"               {item['reason']}")
    if len(items) > limit:
        print(f"    ... 其余 {len(items) - limit} 项")

