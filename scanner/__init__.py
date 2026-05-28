from scanner import temp, recycle, browser, windows_update, logs, hibernate, large_files, duplicates

ALL_SCANNERS = {
    "临时文件": temp,
    "回收站": recycle,
    "浏览器缓存": browser,
    "Windows Update 缓存": windows_update,
    "日志和转储文件": logs,
    "休眠文件": hibernate,
}
