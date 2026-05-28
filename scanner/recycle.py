import ctypes
from ctypes import wintypes


CATEGORY = "回收站"


class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_ulonglong),
        ("i64NumItems", ctypes.c_ulonglong),
    ]


def scan() -> list[dict]:
    """扫描回收站，返回一个汇总条目（回收站需要整体清空）"""
    SHQueryRecycleBinW = ctypes.windll.shell32.SHQueryRecycleBinW
    SHQueryRecycleBinW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(SHQUERYRBINFO)]
    SHQueryRecycleBinW.restype = ctypes.HRESULT

    info = SHQUERYRBINFO()
    info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    hr = SHQueryRecycleBinW(None, ctypes.byref(info))
    if hr != 0:
        return []

    total_size = info.i64Size
    num_items = info.i64NumItems

    if total_size == 0:
        return []

    return [{
        "path": "::recycle_bin",
        "size": total_size,
        "category": CATEGORY,
        "item_count": num_items,
        "special": "recycle_bin",
    }]


def clean_recycle_bin() -> tuple[int, int, int]:
    """清空回收站，返回 (成功标记, 失败标记, 释放字节数)"""
    SHEmptyRecycleBinW = ctypes.windll.shell32.SHEmptyRecycleBinW
    SHEmptyRecycleBinW.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    ]
    SHEmptyRecycleBinW.restype = ctypes.HRESULT

    # SHERB_NOCONFIRMATION = 0x00000001
    # SHERB_NOPROGRESSUI = 0x00000002
    # SHERB_NOSOUND = 0x00000004
    flags = 0x00000001 | 0x00000002 | 0x00000004
    hr = SHEmptyRecycleBinW(None, None, flags)

    items = scan()
    freed = items[0]["size"] if items else 0

    if hr == 0:
        return 1, 0, freed
    return 0, 1, 0
