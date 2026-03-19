# Changelog

All notable changes to opencode-log will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-19

### Changed

- Switched data loading to OpenCode SQLite (`opencode.db`) by default.
- Updated CLI defaults and doctor output to target OpenCode data directory/database.
- Updated docs and tests for database-backed loading.

## [0.3.0] - 2025-03-18

### Added - Major UI/UX Overhaul (Inspired by claude-code-log)

#### 🎨 Interactive Features
- **Timeline Visualization**: Interactive vis-timeline component with:
  - Message grouping by type (user, assistant, tool, reasoning)
  - Click-to-navigate functionality
  - Zoomable and draggable interface
  - Resizable height
  - Filter integration
- **Advanced Search & Filter**: 
  - Inline search with real-time filtering
  - Message type toggle buttons with counts
  - Select all/none actions
  - Search results highlighting
- **Floating Action Buttons**: Quick access toolbar with:
  - Timeline toggle
  - Search/filter panel toggle
  - Details expand/collapse
  - Scroll to top
- **Timezone Conversion**: Automatic conversion of timestamps to user's local timezone
- **Message Folding**: Collapsible content sections with `<details>` elements

#### 🎨 Visual Improvements
- **Modern CSS Components**: Modular component-based styling:
  - `global_styles.css` - Shared base styles
  - `message_styles.css` - Message rendering
  - `filter_styles.css` - Filter toolbar
  - `timeline_styles.css` - Timeline visualization
  - `search_styles.css` - Search components
  - `todo_styles.css` - Todo list styling
  - `project_card_styles.css` - Project cards
  - `session_nav_styles.css` - Session navigation
  - `pygments_styles.css` - Code syntax highlighting
  - `edit_diff_styles.css` - Diff display
  - `page_nav_styles.css` - Pagination
- **Enhanced Card Design**: Modern card-based layouts with shadows and hover effects
- **Responsive Layout**: Improved mobile and desktop responsiveness
- **Better Typography**: Improved readability with refined font sizes and spacing

#### 🚀 CLI Improvements
- **Default Browser Opening**: Now opens browser by default after generation
  - Use `--no-open-browser` to disable (reversed from `--open-browser`)
  - Smart opening: index.html for multiple projects, combined_transcripts.html for single project
- **Positional Argument**: Added `[PROJECT_PATH]` as optional positional argument
  - Replaces `--project-dir` (now deprecated but still supported)
  - Default behavior: process all projects if no path provided
- **Short Options**: Added `-o` for `--output` and `-f` for `--format`
- **New Options**:
  - `--clear-output`: Clear generated HTML/Markdown files before processing
  - `--page-size`: Control pagination (default: 2000 messages per page)
  - `--no-timeline`: Disable timeline visualization for faster generation
  - `--no-syntax-highlight`: Disable code highlighting for faster generation
  - `--no-warnings`: Suppress schema version and other informational warnings
  - `--debug`: Show full error tracebacks
- **Format Normalization**: `--format md` now recognized as alias for `markdown`

#### 📦 Dependencies
- Added `pygments>=2.19.0` for code syntax highlighting
- Added `mistune>=3.1.4` for markdown rendering

#### 📚 Documentation
- Completely rewritten README with:
  - Comprehensive feature list
  - Updated CLI usage examples
  - Advanced usage patterns
  - Bilingual (English/中文) documentation
- Added CHANGELOG.md following Keep a Changelog format

### Changed

#### Template Updates
- Rewrote `transcript.html` with modern layout and all new features
- Rewrote `combined.html` with session grouping and filtering
- Rewrote `index.html` with improved project cards and search
- Added HTML component templates:
  - `timeline.html` - Timeline visualization
  - `search_inline.html` - Inline search input
  - `search_inline_script.html` - Search functionality
  - `search_results_panel.html` - Search results display
  - `session_nav.html` - Session navigation macro
  - `timezone_converter.js` - Timezone conversion

#### Behavior Changes
- Default behavior changed: now processes all projects by default
- Browser opens automatically unless `--no-open-browser` is specified
- Improved error handling with optional debug mode

### Deprecated
- `--project-dir` option (use positional `PROJECT_PATH` instead)
  - Still supported for backward compatibility but hidden from help

### Fixed
- Improved cache key generation for better cache hit rates
- Better handling of missing or invalid data
- More robust error messages

---

## [0.2.0] - Previous Release

### Features
- Basic HTML log generation from OpenCode storage
- Support for todos and session diffs
- Simple caching system
- Markdown output option
- Date range filtering
- Message type rendering (user, assistant, tool, reasoning)

---

## [0.1.0] - Initial Release

### Features
- Basic OpenCode storage parsing
- HTML output generation
- Session and project organization
- Simple message rendering
