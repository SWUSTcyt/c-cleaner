# Windows 磁盘清理工具

C 盘扫系统垃圾，其他固定硬盘（D/E/F 等）按同一套数据盘规则扫描。自动识别盘符，不用手动指定每一块盘。

## 功能

### C 盘（系统垃圾）

- **临时文件** — `%TEMP%`、`Windows\Temp`、`Prefetch`
- **回收站** — 一键清空
- **浏览器缓存** — Chrome / Edge / Firefox
- **Windows Update 缓存** — 系统更新残留
- **日志和转储文件** — `.log`、`.dmp`、WER 报告
- **休眠文件** — 关闭休眠以释放 `hiberfil.sys`（需管理员权限）
- **大文件扫描** — 用户目录下 >100MB 的文件
- **重复文件检测** — 按大小分组后再做 MD5 比对

### 其他盘（数据盘）

自动发现本机固定硬盘（不含系统盘、U 盘），用同一套规则：

- 软件更新缓存（如 `AutoUpdate\Download`）
- 旁边已经解压过的 zip/rar/7z
- 同目录多个版本号文件夹（旧版本需确认后再删）
- 旧版微信目录、Docker 虚拟盘、本地 AI 模型
- 下载目录里的安装包、Steam 跑分/附加工具

扫描结果分成三类：

| 分类 | 含义 | 是否删除 |
|------|------|----------|
| 可安全清理 | 更新缓存、重复压缩包 | 确认后删除 |
| 需要确认 | 旧版本、Docker、模型、安装包等 | 按类勾选后再删 |
| 建议保留 | Steam 游戏、当前微信、pagefile | 不会进入清理 |

C 盘和数据盘分开确认，不会一次删光。

## 使用

需要 Python 3.10+，Windows 10/11，无第三方依赖。

```bash
python main.py
```

- `1` 扫描 C 盘（系统垃圾）
- `2` 扫描其他盘（自动覆盖本机数据盘）
- `3` 扫描全部（先 C 盘确认，再数据盘确认）
- `4` 起为 C 盘单项

只做分析、不删除：

```bash
python disk_analyzer.py          # 系统盘
python disk_analyzer.py --others # 其他数据盘
python disk_analyzer.py E:       # 指定某一块盘（调试用）
```

## 安全与隐私

- 删除前预览，确认后才执行
- 数据盘按类别勾选；建议保留项不会进入清理
- 被进程占用的文件会跳过
- 清理记录写在本地 `cleanup_log.json`，已加入 `.gitignore`，不会上传
- 关闭休眠需要管理员权限

## 项目结构

```
├── main.py                 # CLI 入口
├── disk_analyzer.py        # 磁盘深度分析
├── core/
│   ├── utils.py            # 工具函数
│   ├── drives.py           # 系统盘 / 数据盘发现
│   └── cleaner.py          # 清理执行器
├── scanner/
│   ├── temp.py             # 临时文件
│   ├── recycle.py          # 回收站
│   ├── browser.py          # 浏览器缓存
│   ├── windows_update.py   # Update 缓存
│   ├── logs.py             # 日志文件
│   ├── hibernate.py        # 休眠文件
│   ├── large_files.py      # 大文件扫描
│   ├── duplicates.py       # 重复文件检测
│   └── data_disk.py        # 数据盘已知模式
└── .claude/skills/         # Claude Code skills
```

## Claude Code Skills

### 磁盘深度分析 (`/disk-analysis`)

按系统盘 / 数据盘分开分析。也可直接运行上面的 `disk_analyzer.py`。

### 上下文使用率检查 (`/context-usage`)

查看当前对话的 token 使用率估算。

## License

MIT
