# Upgrade Guide: v0.2.0 → v0.3.0

## Overview

Version 0.3.0 is a major update that brings opencode-log's feature set and user experience in line with claude-code-log. This guide will help you understand the changes and update your workflows.

## Breaking Changes

### 1. Default Behavior Changed

**v0.2.0:**
```bash
# Required explicit flags
opencode-log --all-projects --open-browser
```

**v0.3.0:**
```bash
# Same behavior, now default
opencode-log
```

**What changed:**
- Projects are processed by default if no PROJECT_PATH is specified
- Browser opens automatically after generation
- Use `--no-open-browser` to disable auto-opening

### 2. CLI Parameter Updates

**Deprecated (still works):**
```bash
opencode-log --project-dir /path/to/project --open-browser
```

**New recommended way:**
```bash
opencode-log /path/to/project
```

**What changed:**
- `--project-dir` is now deprecated (use positional `PROJECT_PATH` instead)
- `--open-browser` is now default (use `--no-open-browser` to disable)
- Added short options: `-o` for `--output`, `-f` for `--format`

### 3. Output Format Changes

The generated HTML now uses a completely new template system with:
- Modern CSS variables and component-based styling
- Interactive timeline (requires internet for vis-timeline CDN)
- Enhanced search and filter toolbar
- Floating action buttons

**Impact:** If you have custom CSS overrides, you may need to update them.

## New Features

### Interactive Timeline
```bash
# Enable (default)
opencode-log

# Disable for faster generation
opencode-log --no-timeline
```

The timeline appears at the top of transcript pages and allows you to:
- Visualize message density over time
- Click to jump to specific messages
- Filter by message type
- Resize the timeline height

### Code Syntax Highlighting
```bash
# Enable (default)
opencode-log

# Disable for faster generation
opencode-log --no-syntax-highlight
```

Code blocks now have syntax highlighting powered by Pygments.

### Advanced Search & Filter

The new filter toolbar provides:
- Real-time search across all messages
- Type-based filtering (user, assistant, tool, reasoning)
- Message count display per type
- Select all/none actions

Access via the 🔍 floating button or toolbar.

### Timezone Conversion

All timestamps are now automatically converted to your local timezone.

### Floating Action Buttons

Quick access toolbar in the bottom-right:
- 📆 Toggle timeline
- 🔍 Open search/filter
- 📋 Expand/collapse all details
- 🔝 Scroll to top

## New CLI Options

```bash
# Clean regeneration
opencode-log --clear-cache --clear-output

# Control pagination
opencode-log --page-size 1000

# Performance optimization
opencode-log --no-timeline --no-syntax-highlight

# Debug mode
opencode-log --debug
```

## Migration Checklist

1. **Update your scripts:**
   ```bash
   # Old
   opencode-log --all-projects --open-browser
   
   # New (equivalent)
   opencode-log
   ```

2. **If you use `--project-dir`:**
   ```bash
   # Old
   opencode-log --project-dir /path/to/project
   
   # New
   opencode-log /path/to/project
   ```

3. **If you want to disable browser opening:**
   ```bash
   # Old: (didn't open by default)
   opencode-log --all-projects
   
   # New: (opens by default, add flag to disable)
   opencode-log --no-open-browser
   ```

4. **Clear cache for clean migration:**
   ```bash
   opencode-log --clear-cache --clear-output
   ```

## Performance Considerations

The new features add some overhead. If generation is slow:

1. **Disable optional features:**
   ```bash
   opencode-log --no-timeline --no-syntax-highlight
   ```

2. **Skip todos and diffs:**
   ```bash
   opencode-log --no-todos --no-diffs
   ```

3. **Limit session count:**
   ```bash
   opencode-log --max-sessions 10
   ```

4. **Use cache effectively:**
   ```bash
   # Cache is enabled by default, regenerate only when needed
   opencode-log  # Uses cache
   
   # Force full regeneration when needed
   opencode-log --clear-cache
   ```

## Dependencies

New dependencies added in v0.3.0:
- `pygments>=2.19.0` - Code syntax highlighting
- `mistune>=3.1.4` - Markdown rendering

These are automatically installed when you upgrade.

## Offline Considerations

**Timeline Feature:** The timeline visualization loads vis-timeline from CDN:
```
https://unpkg.com/vis-timeline@latest
```

If you need offline support, you can:
1. Disable timeline: `opencode-log --no-timeline`
2. Or wait for a future version with bundled vis-timeline

## Rollback

If you need to rollback to v0.2.0:

```bash
pip install opencode-log==0.2.0
```

Or with uvx:
```bash
uvx opencode-log@0.2.0
```

## Getting Help

- **Issues:** https://github.com/CatVinci-Studio/opencode-log/issues
- **Docs:** https://catvinci-studio.github.io/opencode-log/
- **Run doctor:** `opencode-log --doctor`
- **Debug mode:** `opencode-log --debug`

## What's Next?

Check out the [CHANGELOG.md](CHANGELOG.md) for a complete list of changes and the [README.md](README.md) for updated documentation and examples.
