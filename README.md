# Lの女性向音声剧 · 结构化总册

将 YouTube 频道 `@mrlovewords9272` 的音频剧内容转写为中文字幕，并结构化整理为「场景 / 台词 / 行为」总册；进一步对台词做错别字校对，并补充角色（说话人）、语气、音效、题材标签、情感弧线等增强标注。

## 目录结构

| 路径 | 说明 |
|---|---|
| `mrlovewords9272_总册.html` | 主总册（225 篇，含搜索 / 目录跳转 / 结构化增强展示，前 10 篇已叠加说话人·语气·音效·分析） |
| `progress.html` | 结构化增强进度看板（45 块状态灯，随时查看进度） |
| `doc_data/videos_simp.json` | 基础台词源（简体，已错别字校对） |
| `doc_data/behavior_simp.json` | 基础场景 / 行为源 |
| `doc_data/chunks/` | 45 个「5 篇/块」处理单元 |
| `doc_data/enriched/` | 已结构化增强的篇目（说话人 / 语气 / 音效 / 篇级分析） |
| `doc_data/progress_status.json` | 进度状态机数据 |
| `*.py` | 数据处理脚本（简体转换 / 错别字校对 / 切块 / 富集 / 渲染） |
| `download_age.bat` + `age_video_ids.txt` | 本机下载年龄墙视频（需本地 yt-dlp + node 环境） |
| `playlist.json` | 频道播放列表元数据（280 视频） |

## 使用说明

- 直接用浏览器打开 `mrlovewords9272_总册.html` 即可浏览全部内容。
- **年龄墙视频（55 个）** 仍待补充：需在本机运行 `download_age.bat`（依赖 yt-dlp 与 node，且需有效的 YouTube cookies）下载后转写并入册。

## 重要说明

- 🔒 **凭证安全**：YouTube cookies 文件已通过 `.gitignore` 排除，绝不会进入仓库。
- ⚠️ **内容提示**：本项目为女性向音声剧，含敏感亲密措辞，建议将仓库设为**私有**。
