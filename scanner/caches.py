"""C 盘可重下的包缓存 / 异常备份，对应分析器里的已知清理目标。"""

import os
from core.utils import get_dir_size

CATEGORY = "已知缓存"
MIN_SIZE = 10 * 1024 * 1024

# (相对用户主目录的路径, 说明)
SAFE_TARGETS = [
    (".cache/huggingface", "HuggingFace 缓存，可重新下载"),
    (".cache/torch", "PyTorch 缓存"),
    (".conda/pkgs", "Conda 包缓存"),
    ("AppData/Local/uv", "uv 包缓存"),
    ("AppData/Local/Yarn", "Yarn 缓存"),
    ("AppData/Local/npm", "npm 缓存"),
    ("AppData/Local/pip", "pip 缓存"),
    ("AppData/Roaming/LarkShell.exception_backup", "飞书异常备份"),
    ("AppData/Local/Ollama/updates", "Ollama 更新安装包残留"),
    ("AppData/Roaming/io.github.clash-verge-rev.clash-verge-rev/logs", "Clash 日志"),
]


def _abs_path(home: str, rel: str) -> str:
    return os.path.join(home, rel.replace("/", os.sep))


def scan() -> list[dict]:
    """扫描可安全清理的已知缓存目录。"""
    home = os.path.expanduser("~")
    results = []
    for rel, reason in SAFE_TARGETS:
        full = _abs_path(home, rel)
        if not os.path.exists(full):
            continue
        try:
            size = get_dir_size(full) if os.path.isdir(full) else os.path.getsize(full)
        except OSError:
            continue
        if size < MIN_SIZE:
            continue
        results.append({
            "path": full,
            "size": size,
            "category": CATEGORY,
            "reason": reason,
        })
    results.sort(key=lambda x: x["size"], reverse=True)
    return results
