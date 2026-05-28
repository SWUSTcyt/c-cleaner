import os
from core.utils import is_admin


CATEGORY = "休眠文件"

HIBERFIL_PATH = os.path.join(os.environ.get("SystemDrive", "C:"), os.sep, "hiberfil.sys")


def scan() -> list[dict]:
    """检测休眠文件"""
    if not os.path.isfile(HIBERFIL_PATH):
        return []
    try:
        size = os.path.getsize(HIBERFIL_PATH)
    except OSError:
        return []

    return [{
        "path": HIBERFIL_PATH,
        "size": size,
        "category": CATEGORY,
        "special": "hibernate",
        "need_admin": not is_admin(),
    }]


def disable_hibernate() -> tuple[bool, str]:
    """关闭休眠并删除 hiberfil.sys，需要管理员权限"""
    if not is_admin():
        return False, "需要管理员权限才能关闭休眠功能"

    import subprocess
    try:
        result = subprocess.run(
            ["powercfg", "/hibernate", "off"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "休眠已关闭，hiberfil.sys 已删除"
        return False, f"关闭休眠失败: {result.stderr}"
    except Exception as e:
        return False, f"执行失败: {e}"
