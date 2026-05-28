import os
from core.utils import scan_dir_files, get_dir_size


CATEGORY = "浏览器缓存"

# 浏览器缓存目录
BROWSER_CACHE_DIRS = {
    "Chrome": [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "Cache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "Code Cache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "GPUCache"),
    ],
    "Edge": [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data", "Default", "Cache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data", "Default", "Code Cache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data", "Default", "GPUCache"),
    ],
    "Firefox": [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Mozilla", "Firefox", "Profiles"),
    ],
}


def _scan_firefox_profiles(base_dir: str) -> list[dict]:
    """扫描 Firefox 的 profile 缓存目录"""
    results = []
    if not os.path.isdir(base_dir):
        return results
    try:
        for profile in os.scandir(base_dir):
            if profile.is_dir():
                cache_dir = os.path.join(profile.path, "cache2", "entries")
                if os.path.isdir(cache_dir):
                    for file_path in scan_dir_files(cache_dir):
                        try:
                            size = os.path.getsize(file_path)
                        except OSError:
                            continue
                        results.append({
                            "path": file_path,
                            "size": size,
                            "category": CATEGORY,
                        })
    except (PermissionError, OSError):
        pass
    return results


def scan() -> list[dict]:
    """扫描浏览器缓存"""
    results = []

    for browser_name, dirs in BROWSER_CACHE_DIRS.items():
        for cache_dir in dirs:
            if not cache_dir or not os.path.isdir(cache_dir):
                continue

            if browser_name == "Firefox":
                results.extend(_scan_firefox_profiles(cache_dir))
            else:
                for file_path in scan_dir_files(cache_dir):
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
