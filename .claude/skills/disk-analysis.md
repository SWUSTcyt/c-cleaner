---
name: disk-analysis
description: 深度分析磁盘空间占用，找出可清理的大文件和目录
---

# 磁盘深度分析 Skill

当用户要求分析磁盘空间、查找大文件、找出可清理内容时，按「系统盘 / 数据盘」分开分析，不要混在一次确认里删除。

在仓库根目录运行下面的命令。

## 怎么跑

```bash
python disk_analyzer.py              # 系统盘 C：AppData、缓存、用户目录
python disk_analyzer.py --others     # 其他固定硬盘（自动发现 D/E/F，不含 U 盘）
python disk_analyzer.py E:           # 只看指定数据盘（调试）
```

交互清理用 `python main.py`：`1` 扫 C 盘，`2` 扫其他盘，`3` 全部（两次确认）。

## 系统盘（C）要点

1. 磁盘总览
2. 根目录 TOP 10
3. 用户目录 TOP 10（AppData、.conda、.cache、Downloads）
4. AppData Local / Roaming TOP 8
5. 已知缓存：HF / Torch / Conda pkgs / uv / Yarn / npm / pip（`python main.py` 选项 1 可清）
6. Conda 环境、WSL 虚拟盘等只报告，删除需确认
7. 用户目录 >500MB 文件（不要跳过 `.cache`、`.lmstudio` 等点目录）

## 数据盘要点

用 `scanner/data_disk.py` 的已知模式，输出三类：

- **可安全清理**：更新缓存、旁边已有解压目录的压缩包
- **需要确认**：软件旧版本、旧版微信、QQ 聊天记录、Docker、本地模型、安装包、Steam 附加工具
- **建议保留**：Steam 游戏、当前微信、pagefile（不要删）

聊天记录（QQ/微信自定义数据目录）：只清空内容，必须保留文件夹。删掉整个目录后，软件会找不到原路径，可能把记录写回 C 盘文档。

## 注意事项

- 跳过系统关键目录和 PermissionError
- 数据盘全盘索引可能需要几分钟
- 输出用 `format_size`，中文
