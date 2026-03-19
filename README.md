# opencode-log

`opencode-log` is a powerful CLI tool that turns local OpenCode sessions into clean, interactive, and searchable HTML logs with advanced visualization features.

[GitHub Repository](https://github.com/CatVinci-Studio/opencode-log) | [Issues](https://github.com/CatVinci-Studio/opencode-log/issues) | [Docs / GitHub Pages](https://catvinci-studio.github.io/opencode-log/)

---

## English

### What It Does

`opencode-log` reads OpenCode local storage and generates a rich, interactive browsable site with:

- A global `index.html` with project cards and statistics
- Per-project `combined_transcripts.html` with all sessions combined
- Per-session `session-<id>.html` files for detailed review
- Full Markdown export support for lightweight sharing

It is designed for reviewing long coding sessions, tool traces, reasoning blocks, token/cost usage, and project evolution over time.

### Key Features

#### 🎨 **Modern, Interactive UI**
- **Timeline Visualization**: Interactive, zoomable timeline (vis-timeline) with message grouping and click-to-navigate
- **Advanced Search & Filter**: Real-time search with message type filtering (user, assistant, tool, reasoning)
- **Floating Action Buttons**: Quick access to timeline, search, details toggle, and scroll-to-top
- **Timezone Conversion**: Automatic conversion of all timestamps to local timezone
- **Responsive Design**: Works seamlessly on desktop and mobile devices

#### 📊 **Rich Content Rendering**
- **Syntax Highlighting**: Code blocks with Pygments syntax highlighting for multiple languages
- **Markdown Support**: Full markdown rendering with mistune
- **Message Folding**: Collapsible tool calls, reasoning blocks, and nested content
- **Message Types**: Support for user/assistant messages, tool use/results, thinking content, and more

#### 💾 **OpenCode-Specific Features**
- **Todo Lists**: Display session todo items from `storage/todo/*.json`
- **Session Diffs**: Show file changes with additions/deletions from `storage/session_diff/*.json`
- **Token Metrics**: Track input/output/reasoning/cache tokens per message and session
- **Cost Tracking**: Calculate and display session and project costs

#### ⚡ **Performance & Efficiency**
- **Smart Caching**: Parsed session cache and render signature cache (skip unchanged pages)
- **Lazy Loading**: Timeline and syntax highlighting load on-demand
- **Pagination Support**: Large sessions automatically split into manageable pages
- **Incremental Rendering**: Only regenerate changed files

#### 🔍 **Data Analysis**
- **Date Range Filtering**: Natural language date filtering (e.g., "7 days ago", "yesterday")
- **Session Statistics**: Message count, tool usage, token consumption, and cost per session
- **Project Overview**: Aggregate statistics across all projects and sessions
- **Search History**: Browser-side search with instant results

### Installation

#### Option A: Local development install

```bash
cd opencode-log
pip install -e .
```

#### Option B: Run with `uvx` from local path

```bash
uvx --from /path/to/opencode-log opencode-log --help
```

#### Option C: Run with `uvx` from PyPI (after release)

```bash
uvx opencode-log --help
```

### Quick Start

```bash
# Process all projects and open in browser (default behavior)
opencode-log

# Process all projects without opening browser
opencode-log --no-open-browser

# Process specific project
opencode-log /path/to/your/project

# Filter by date range with natural language
opencode-log --from-date "7 days ago" --to-date "today"

# Generate both HTML and Markdown
opencode-log --format both

# Check environment and storage
opencode-log --doctor
```

### CLI Options

```text
Positional Arguments:
  [PROJECT_PATH]                Optional path to specific project directory

Storage & Input:
  --storage-dir PATH            OpenCode storage directory
                                [default: ~/.local/share/opencode/storage]

Output Control:
  -o, --output PATH             Output directory [default: ./opencode-logs]
  -f, --format [html|md|markdown|both]
                                Output format [default: html]

Project Selection:
  --all-projects                Process all projects (default if no PROJECT_PATH)
  --max-sessions INTEGER        Limit sessions per project

Date Filtering:
  --from-date TEXT              Filter from date (e.g., "2 hours ago", "yesterday")
  --to-date TEXT                Filter to date (e.g., "1 hour ago", "today")

Session Control:
  --no-individual-sessions      Skip individual session files
  --page-size INTEGER           Messages per page [default: 2000]

Cache Management:
  --no-cache                    Disable caching
  --clear-cache                 Clear cache before processing
  --clear-output                Clear output files before processing

Browser:
  --no-open-browser             Don't open browser after generation
                                (default is to auto-open)

Feature Toggles:
  --no-todos                    Skip loading/rendering todos
  --no-diffs                    Skip loading/rendering diffs
  --no-timeline                 Disable timeline visualization
  --no-syntax-highlight         Disable code syntax highlighting

Debugging:
  --doctor                      Run environment checks and exit
  --debug                       Show full traceback on errors
```

### Advanced Examples

```bash
# Fast generation: disable optional features
opencode-log --no-timeline --no-syntax-highlight --no-todos --no-diffs

# Clean regeneration
opencode-log --clear-cache --clear-output

# Export to markdown for sharing
opencode-log --format markdown -o ./export

# Process recent sessions only
opencode-log --from-date "last week" --max-sessions 10

# Single project with custom output
opencode-log /path/to/project -o ./my-project-logs
```

### Output Structure

```text
opencode-logs/
├── index.html
├── projects/
│   ├── <project-slug>/
│   │   ├── combined_transcripts.html
│   │   ├── session-<id>.html
│   │   └── ...
└── .opencode-log-cache/
    ├── state.json
    └── sessions/
```

### Notes

- Primary data source is OpenCode internal storage.
- Storage schema is internal and may change in future OpenCode versions.
- Cache files live under `<output>/.opencode-log-cache/`.

### Common Warnings

#### Multiple Session Schema Versions

If you see:
```
Warning: multiple session schema versions detected: 1.1.32, 1.1.34, ...
```

**This is normal!** It means you've used different versions of OpenCode over time. opencode-log automatically handles all versions and this warning is informational only.

**To hide the warning:**
```bash
opencode-log --no-warnings
```

**Why it happens:**
- OpenCode evolves its storage format across versions
- Your historical sessions remain in the storage directory
- Each session records the OpenCode version that created it

**Impact:** None. All versions are fully supported and compatible.

### Release to PyPI

Recommended (GitHub Actions + Trusted Publishing):

1. In PyPI project settings, add a Trusted Publisher for this repo:
   - Owner: `CatVinci-Studio`
   - Repository: `opencode-log`
   - Workflow: `.github/workflows/release.yml`
   - Environment: `pypi`
2. Publish to PyPI by either:
   - manually running workflow **Release Python Package**, or
   - creating and pushing a version tag (for example `v0.3.1`).

```bash
git tag v0.3.1
git push origin v0.3.1
```

Optional local publish (token-based):

```bash
# 1) Build
uv build

# 2) Validate package metadata
uvx twine check dist/*

# 3) Upload to PyPI
uvx twine upload dist/*
```

### GitHub Pages (Project Website)

You can host docs/examples on GitHub Pages from this repository.

Recommended setup:

1. Push repository to: `https://github.com/CatVinci-Studio/opencode-log`
2. In GitHub repo settings, open **Pages**
3. Set source to **GitHub Actions**
4. Add a docs workflow (or publish static files from `docs/`)
5. Site URL will be:
   `https://catvinci-studio.github.io/opencode-log/`

---

## 中文

### 项目介绍

`opencode-log` 是一个功能强大的 CLI 工具，用于将本地 OpenCode 会话转换成交互式、可搜索的 HTML 日志网站，并提供高级可视化功能。

它会生成：

- 全局索引页 `index.html` 及项目卡片统计
- 每个项目的 `combined_transcripts.html`（合并所有会话）
- 每个会话的 `session-<id>.html` 详细页面
- 完整的 Markdown 导出支持，便于分享

适合用于回看长对话、工具调用过程、reasoning 内容、token/cost 使用情况，以及项目演进历史。

### 核心功能

#### 🎨 **现代化交互界面**
- **时间线可视化**：交互式、可缩放的时间线（vis-timeline），支持消息分组和点击导航
- **高级搜索与过滤**：实时搜索，支持按消息类型过滤（用户、助手、工具、推理）
- **悬浮操作按钮**：快速访问时间线、搜索、详情切换和回到顶部
- **时区转换**：自动将所有时间戳转换为本地时区显示
- **响应式设计**：在桌面和移动设备上无缝工作

#### 📊 **丰富内容渲染**
- **语法高亮**：使用 Pygments 为多种编程语言提供代码高亮
- **Markdown 支持**：使用 mistune 进行完整 markdown 渲染
- **消息折叠**：可折叠的工具调用、推理块和嵌套内容
- **消息类型**：支持用户/助手消息、工具使用/结果、思考内容等

#### 💾 **OpenCode 专属功能**
- **Todo 列表**：显示来自 `storage/todo/*.json` 的会话任务
- **会话 Diff**：展示来自 `storage/session_diff/*.json` 的文件变更（增加/删除行数）
- **Token 指标**：跟踪每条消息和会话的输入/输出/推理/缓存 token
- **成本追踪**：计算并显示会话和项目成本

#### ⚡ **性能与效率**
- **智能缓存**：解析会话缓存和渲染签名缓存（跳过未变化的页面）
- **按需加载**：时间线和语法高亮按需加载
- **分页支持**：大型会话自动分页为可管理的页面
- **增量渲染**：仅重新生成已更改的文件

#### 🔍 **数据分析**
- **日期范围过滤**：自然语言日期过滤（如 "7 days ago"、"yesterday"）
- **会话统计**：每个会话的消息数、工具使用、token 消耗和成本
- **项目概览**：跨所有项目和会话的汇总统计
- **搜索历史**：浏览器端搜索，即时结果

### 安装方式

#### 方式 A：本地开发安装

```bash
cd opencode-log
pip install -e .
```

#### 方式 B：使用 `uvx` 运行本地项目

```bash
uvx --from /path/to/opencode-log opencode-log --help
```

#### 方式 C：发布后直接 `uvx` 运行

```bash
uvx opencode-log --help
```

### 快速开始

```bash
# 处理全部项目并自动打开浏览器（默认行为）
opencode-log

# 处理全部项目但不打开浏览器
opencode-log --no-open-browser

# 处理指定项目
opencode-log /你的项目路径

# 用自然语言过滤日期范围
opencode-log --from-date "7 days ago" --to-date "today"

# 同时生成 HTML 和 Markdown
opencode-log --format both

# 环境检查
opencode-log --doctor
```

### CLI 参数说明

```text
位置参数：
  [PROJECT_PATH]                可选的项目目录路径

存储与输入：
  --storage-dir PATH            OpenCode 存储目录
                                [默认: ~/.local/share/opencode/storage]

输出控制：
  -o, --output PATH             输出目录 [默认: ./opencode-logs]
  -f, --format [html|md|markdown|both]
                                输出格式 [默认: html]

项目选择：
  --all-projects                处理所有项目（未指定 PROJECT_PATH 时为默认）
  --max-sessions INTEGER        限制每个项目的会话数

日期过滤：
  --from-date TEXT              起始日期（如 "2 hours ago"、"yesterday"）
  --to-date TEXT                结束日期（如 "1 hour ago"、"today"）

会话控制：
  --no-individual-sessions      跳过单独会话文件
  --page-size INTEGER           每页最大消息数 [默认: 2000]

缓存管理：
  --no-cache                    禁用缓存
  --clear-cache                 处理前清除缓存
  --clear-output                处理前清除输出文件

浏览器：
  --no-open-browser             生成后不打开浏览器
                                （默认会自动打开）

功能开关：
  --no-todos                    跳过 todo 加载/渲染
  --no-diffs                    跳过 diff 加载/渲染
  --no-timeline                 禁用时间线可视化
  --no-syntax-highlight         禁用代码语法高亮

调试：
  --doctor                      运行环境检查并退出
  --debug                       显示完整错误堆栈
```

### 高级示例

```bash
# 快速生成：禁用可选功能
opencode-log --no-timeline --no-syntax-highlight --no-todos --no-diffs

# 完全重新生成
opencode-log --clear-cache --clear-output

# 导出为 Markdown 用于分享
opencode-log --format markdown -o ./导出

# 只处理最近的会话
opencode-log --from-date "上周" --max-sessions 10

# 单个项目自定义输出
opencode-log /项目路径 -o ./我的项目日志
```

### 输出目录结构

```text
opencode-logs/
├── index.html
├── projects/
│   ├── <project-slug>/
│   │   ├── combined_transcripts.html
│   │   ├── session-<id>.html
│   │   └── ...
└── .opencode-log-cache/
    ├── state.json
    └── sessions/
```

### 说明

- 当前主要依赖 OpenCode 内部存储格式。
- 内部存储结构后续可能变化，建议关注兼容性。
- 缓存目录位于 `<output>/.opencode-log-cache/`。

### 常见警告

#### 多个会话架构版本

如果看到：
```
Warning: multiple session schema versions detected: 1.1.32, 1.1.34, ...
```

**这是正常的！** 这意味着你在不同时间使用了不同版本的 OpenCode。opencode-log 会自动处理所有版本，此警告仅供参考。

**隐藏警告：**
```bash
opencode-log --no-warnings
```

**原因：**
- OpenCode 在不同版本间会演进其存储格式
- 历史会话仍保留在存储目录中
- 每个会话都记录了创建它的 OpenCode 版本

**影响：** 无。所有版本都完全支持和兼容。

### 发布到 PyPI

推荐使用 GitHub Actions + Trusted Publishing（无需在仓库保存 PyPI Token）：

1. 在 PyPI 项目设置中添加 Trusted Publisher：
   - Owner: `CatVinci-Studio`
   - Repository: `opencode-log`
   - Workflow: `.github/workflows/release.yml`
   - Environment: `pypi`
2. 发布到 PyPI 的方式：
   - 手动触发 **Release Python Package** 工作流；或
   - 创建并推送版本标签（如 `v0.3.1`）

```bash
git tag v0.3.1
git push origin v0.3.1
```

本地发布（Token 方式，可选）：

```bash
# 1) 构建
uv build

# 2) 包体校验
uvx twine check dist/*

# 3) 发布到 PyPI
uvx twine upload dist/*
```

### GitHub 仓库与网站

建议仓库地址：

- `https://github.com/CatVinci-Studio/opencode-log`

建议开启 GitHub Pages，用于项目网站/文档展示：

- 站点地址：`https://catvinci-studio.github.io/opencode-log/`
