# opencode-log

`opencode-log` is a CLI tool that converts local OpenCode sessions into interactive, searchable HTML/Markdown logs.

It now reads data directly from OpenCode's SQLite database (`opencode.db`) by default.

[![PyPI version](https://img.shields.io/pypi/v/opencode-log.svg)](https://pypi.org/project/opencode-log/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/CatVinci-Studio/opencode-log/actions/workflows/release.yml/badge.svg)](https://github.com/CatVinci-Studio/opencode-log/actions/workflows/release.yml)
[![Wheel](https://img.shields.io/pypi/wheel/opencode-log.svg)](https://pypi.org/project/opencode-log/)

中文文档: [README.zh.md](README.zh.md)

## Key Features

- Interactive timeline, search, and message-type filtering
- Rich rendering for text, code, reasoning, and tool calls
- OpenCode-specific support for todos, session diffs, tokens, and cost
- Incremental rendering with cache for faster regeneration

## Install

Recommended: run directly with `uvx`.

```bash
uvx opencode-log
```

Or install with pip:

```bash
pip install opencode-log
```

## Quick Start

```bash
# Process all projects (default: opens browser)
opencode-log

# Explicitly point to OpenCode data directory (contains opencode.db)
opencode-log --storage-dir ~/.local/share/opencode

# Or point directly to the database file
opencode-log --storage-dir ~/.local/share/opencode/opencode.db

# Process all projects without opening browser
opencode-log --no-open-browser

# Filter by date with natural language
opencode-log --from-date "7 days ago" --to-date "today"

# Generate both HTML and Markdown
opencode-log --format both
```

## Contact

📫ChengAo: `chengao_shen@ieee.org`

## License

MIT. See [LICENSE](LICENSE).
