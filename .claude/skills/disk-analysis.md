---
name: disk-analysis
description: 深度分析磁盘空间占用，找出可清理的大文件和目录
---

# 磁盘深度分析 Skill

当用户要求分析磁盘空间、查找大文件、找出可清理内容时，执行以下分析流程。

## 分析步骤

### 1. 磁盘总览
运行 Python 脚本检查目标磁盘的总容量、已用空间、剩余空间。

### 2. 根目录扫描
扫描磁盘根目录下各文件夹大小，按从大到小排序，展示 TOP 10。

### 3. 用户目录深入（重点区域）
扫描 `C:\Users\<用户名>\` 下各文件夹大小，按从大到小排序，展示 TOP 10。
重点关注：AppData、.conda、.cache、Downloads、Desktop

### 4. AppData 分层分析
分别扫描 `AppData\Local` 和 `AppData\Roaming` 下各子目录大小，各展示 TOP 8。

### 5. 已知高频清理目标检查
检查以下目录是否存在并报告大小：
- `.cache\huggingface` — HF 模型缓存
- `.cache\torch` — PyTorch 缓存
- `.conda\envs` — Conda 环境（列出各环境大小）
- `.conda\pkgs` — Conda 包缓存
- `AppData\Local\uv` — uv 包管理缓存
- `AppData\Local\Yarn` — Yarn 缓存
- `AppData\Local\npm` — npm 缓存
- `AppData\Local\pip` — pip 缓存
- 回收站大小

### 6. 大文件扫描
扫描用户目录下大于 500MB 的文件，按大小排序，展示 TOP 20。

### 7. 输出报告
输出结构化的分析报告，分为三类：
- **可安全清理**：纯缓存/日志，删除不影响功能
- **需要确认**：可能有用但占用大的项目（旧环境、WSL 等）
- **建议转移**：大文件，可移到其他盘

## 实现方式

使用项目内 `core/utils.py` 中的工具函数：
- `format_size()` — 格式化字节大小
- `get_dir_size()` — 计算目录大小
- `scan_dir_files()` — 扫描目录文件

分析脚本直接在 `F:\working\pj-cpan-clean` 目录下用 `python -c` 运行，
所有路径使用 Python 风格（`C:/Users/...`），输出中文。

## 注意事项
- 跳过系统关键目录（Windows、System32 等）
- 跳过被占用的文件（PermissionError 静默跳过）
- 大目录扫描可能需要几分钟，使用后台任务（run_in_background）
- 输出时用 `format_size` 格式化所有大小数字
