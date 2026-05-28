# C盘清理工具

Windows C盘空间清理工具，支持扫描和清理各类系统垃圾文件，帮助释放磁盘空间。

## 功能

- **临时文件** — 清理 `%TEMP%`、`Windows\Temp`、`Prefetch`
- **回收站** — 一键清空回收站
- **浏览器缓存** — Chrome / Edge / Firefox 缓存
- **Windows Update 缓存** — 系统更新残留文件
- **日志和转储文件** — `.log`、`.dmp`、WER 报告
- **休眠文件** — 关闭休眠释放 `hiberfil.sys`（需管理员权限）
- **大文件扫描** — 扫描 >100MB 的大文件
- **重复文件检测** — 基于 MD5 哈希比对
- **磁盘深度分析** — 全面分析磁盘空间占用，找出可清理项

## 使用

### 清理工具

```bash
python main.py
```

按菜单选择扫描类别，查看扫描结果后确认清理。

### 磁盘分析

```bash
python disk_analyzer.py          # 分析 C 盘
python disk_analyzer.py D:/      # 分析指定盘符
```

## 安全机制

- 删除前预览，确认后才执行
- 自动跳过被进程占用的文件
- 所有删除操作记录到 `cleanup_log.json`
- 休眠功能需管理员权限

## 环境要求

- Windows 10/11
- Python 3.10+
- 无需安装第三方依赖

## 项目结构

```
├── main.py                 # CLI 入口
├── disk_analyzer.py        # 磁盘深度分析
├── core/
│   ├── utils.py            # 工具函数
│   └── cleaner.py          # 清理执行器
├── scanner/
│   ├── temp.py             # 临时文件
│   ├── recycle.py          # 回收站
│   ├── browser.py          # 浏览器缓存
│   ├── windows_update.py   # Update 缓存
│   ├── logs.py             # 日志文件
│   ├── hibernate.py        # 休眠文件
│   ├── large_files.py      # 大文件扫描
│   └── duplicates.py       # 重复文件检测
└── .claude/
    └── skills/
        ├── disk-analysis.md   # 磁盘深度分析 skill
        └── context-usage.md   # 上下文使用率检查 skill
```

## Claude Code Skills

本项目包含为 Claude Code 设计的 skill 文件，位于 `.claude/skills/` 目录。

### 磁盘深度分析 (`/disk-analysis`)

在 Claude Code 中输入 `/disk-analysis`，将自动执行完整的磁盘空间分析流程：

1. **磁盘总览** — 容量、已用、剩余空间
2. **根目录扫描** — 各文件夹大小 TOP 10
3. **用户目录深入** — AppData、.conda、.cache 等重点区域
4. **AppData 分层分析** — Local / Roaming 子目录 TOP 8
5. **高频清理目标检查** — HuggingFace 缓存、PyTorch 缓存、Conda 环境、npm/pip/Yarn/uv 缓存等
6. **大文件扫描** — 用户目录下 >500MB 文件 TOP 20
7. **分类报告** — 分为「可安全清理」「需要确认」「建议转移」三类

扫描过程中使用后台任务，大目录可能需要几分钟。

### 上下文使用率检查 (`/context-usage`)

在 Claude Code 中输入 `/context-usage`，可查看当前对话的 token 使用率和剩余空间。

## License

MIT
