import os
import ctypes
import shutil


def format_size(size_bytes: int) -> str:
    """将字节数转换为人类可读的大小字符串"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def is_admin() -> bool:
    """检查当前进程是否以管理员权限运行"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def safe_delete(file_path: str) -> bool:
    """安全删除单个文件，跳过占用中或权限不足的文件，成功返回 True"""
    try:
        os.remove(file_path)
        return True
    except (PermissionError, OSError):
        return False


def safe_delete_dir(dir_path: str) -> bool:
    """安全删除目录，跳过占用中或权限不足的目录"""
    try:
        shutil.rmtree(dir_path)
        return True
    except (PermissionError, OSError):
        return False


def get_dir_size(dir_path: str) -> int:
    """计算目录总大小（字节），跳过无法访问的文件"""
    total = 0
    try:
        for entry in os.scandir(dir_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_dir_size(entry.path)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return total


def scan_dir_files(dir_path: str, extensions: list[str] | None = None) -> list[str]:
    """递归扫描目录下的文件路径，可按扩展名过滤"""
    files = []
    try:
        for entry in os.scandir(dir_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    if extensions is None or os.path.splitext(entry.name)[1].lower() in extensions:
                        files.append(entry.path)
                elif entry.is_dir(follow_symlinks=False):
                    files.extend(scan_dir_files(entry.path, extensions))
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return files
