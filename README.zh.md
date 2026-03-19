# opencode-log（中文）

`opencode-log` 是一个 CLI 工具，用于将本地 OpenCode 会话转换为可交互、可搜索的 HTML/Markdown 日志。

现在默认直接读取 OpenCode 的 SQLite 数据库（`opencode.db`）。

[![PyPI version](https://img.shields.io/pypi/v/opencode-log.svg)](https://pypi.org/project/opencode-log/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/CatVinci-Studio/opencode-log/actions/workflows/release.yml/badge.svg)](https://github.com/CatVinci-Studio/opencode-log/actions/workflows/release.yml)
[![Wheel](https://img.shields.io/pypi/wheel/opencode-log.svg)](https://pypi.org/project/opencode-log/)

- English docs: [README.md](README.md)

## 核心功能

- 交互式时间线、实时搜索与消息类型过滤
- 对文本、代码、推理与工具调用的丰富渲染
- 支持 OpenCode 专属数据：todo、session diff、token 与成本
- 基于缓存的增量渲染，提升重复生成速度

## 安装

推荐直接使用 `uvx`：

```bash
uvx opencode-log
```

或使用 pip 安装：

```bash
pip install opencode-log
```

## 快速开始

```bash
# 处理全部项目（默认会打开浏览器）
opencode-log

# 显式指定 OpenCode 数据目录（包含 opencode.db）
opencode-log --storage-dir ~/.local/share/opencode

# 或直接指定数据库文件
opencode-log --storage-dir ~/.local/share/opencode/opencode.db

# 处理全部项目但不打开浏览器
opencode-log --no-open-browser

# 使用自然语言进行日期过滤
opencode-log --from-date "7 days ago" --to-date "today"

# 同时生成 HTML 和 Markdown
opencode-log --format both
```

## 联系方式

📫 ChengAo: `chengao_shen@ieee.org`

## 许可证

MIT，详见 [LICENSE](LICENSE)。
