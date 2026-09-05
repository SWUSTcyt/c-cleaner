"""磁盘发现：系统盘 vs 数据盘（固定硬盘，不含 U 盘）。"""

import ctypes
import os
import string


DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3

_GetDriveTypeW = ctypes.windll.kernel32.GetDriveTypeW
_GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
_GetDriveTypeW.restype = ctypes.c_uint


def _root(letter: str) -> str:
    return f"{letter.upper()}:\\"


def system_drive() -> str:
    """系统盘根路径，例如 C:\\"""
    raw = os.environ.get("SystemDrive", "C:")
    letter = raw.rstrip(":\\/")[:1] or "C"
    return _root(letter)


def list_fixed_drives() -> list[str]:
    """本机所有固定硬盘根路径，例如 ['C:\\', 'E:\\']"""
    drives = []
    for letter in string.ascii_uppercase:
        root = _root(letter)
        if _GetDriveTypeW(root) == DRIVE_FIXED:
            drives.append(root)
    return drives


def data_drives() -> list[str]:
    """除系统盘外的固定硬盘。"""
    sys_root = system_drive().upper()
    return [d for d in list_fixed_drives() if d.upper() != sys_root]


def normalize_root(drive: str) -> str:
    """把 E / E: / E:/ 规范成 E:\\"""
    letter = drive.strip().rstrip(":\\/").replace("/", "")[:1]
    if not letter:
        return system_drive()
    return _root(letter)


def format_drive_list(drives: list[str]) -> str:
    if not drives:
        return "无"
    return "  ".join(d.rstrip("\\") for d in drives)
