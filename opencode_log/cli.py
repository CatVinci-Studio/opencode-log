from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
import shutil
from typing import Optional

import click

from .cache import CacheManager
from .markdown import (
    markdown_render_signature,
    render_combined_markdown,
    render_index_markdown,
    render_session_markdown,
)
from .models import Project
from .render import (
    combined_render_signature,
    index_render_signature,
    render_combined_page,
    render_index_page,
    render_session_page,
    session_render_signature,
)
from .storage import (
    get_storage_schema_warnings,
    load_project_sessions,
    load_projects,
    parse_date_to_ms,
    safe_slug,
)


def _default_storage_dir() -> Path:
    return Path.home() / ".local" / "share" / "opencode"


def _pick_projects(
    projects: list[Project], input_path: Path | None, all_projects: bool
) -> list[Project]:
    """Pick projects based on input path or all_projects flag."""
    if all_projects or not input_path:
        return projects
    target = str(input_path.resolve())
    return [p for p in projects if str(Path(p.worktree).resolve()) == target]


def _clear_output_files(output_dir: Path, file_ext: str) -> None:
    """Clear generated output files."""
    try:
        # Clear index file
        index_file = output_dir / f"index.{file_ext}"
        if index_file.exists():
            index_file.unlink()
            click.echo(f"Removed {index_file}")

        # Clear project files
        projects_dir = output_dir / "projects"
        if projects_dir.exists():
            output_files = list(projects_dir.glob(f"**/*.{file_ext}"))
            for output_file in output_files:
                output_file.unlink()
            if output_files:
                click.echo(f"Removed {len(output_files)} {file_ext.upper()} files")
    except Exception as e:
        click.echo(f"Warning: Failed to clear {file_ext.upper()} files: {e}")


@click.command()
@click.argument(
    "input_path",
    type=click.Path(path_type=Path),
    required=False,
    metavar="[PROJECT_PATH]",
)
@click.option(
    "--storage-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="OpenCode data directory or opencode.db path (default: ~/.local/share/opencode)",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=Path("./opencode-logs"),
    show_default=True,
    help="Output directory",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["html", "md", "markdown", "both"], case_sensitive=False),
    default="html",
    show_default=True,
    help="Output format: html, md/markdown, or both",
)
@click.option(
    "--all-projects",
    is_flag=True,
    help="Process all projects in OpenCode data source",
)
@click.option(
    "--from-date",
    type=str,
    help='Filter messages from date/time (e.g., "2 hours ago", "yesterday", "2025-06-08")',
)
@click.option(
    "--to-date",
    type=str,
    help='Filter messages up to date/time (e.g., "1 hour ago", "today", "2025-06-08 15:00")',
)
@click.option(
    "--max-sessions",
    type=int,
    default=None,
    help="Maximum sessions per project",
)
@click.option(
    "--no-individual-sessions",
    is_flag=True,
    help="Skip generating individual session files (only create combined transcript)",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable caching and force reprocessing of all files",
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="Clear cache before processing",
)
@click.option(
    "--clear-output",
    is_flag=True,
    help="Clear generated output files (HTML/Markdown) before processing",
)
@click.option(
    "--no-open-browser",
    is_flag=True,
    help="Don't open the browser after generation (default is to open)",
)
@click.option(
    "--no-todos",
    is_flag=True,
    help="Skip loading and rendering session todo files",
)
@click.option(
    "--no-diffs",
    is_flag=True,
    help="Skip loading and rendering session diffs",
)
@click.option(
    "--page-size",
    type=int,
    default=2000,
    show_default=True,
    help="Maximum messages per page for combined transcript (sessions are never split)",
)
@click.option(
    "--no-timeline",
    is_flag=True,
    help="Disable timeline visualization (improves generation speed)",
)
@click.option(
    "--no-syntax-highlight",
    is_flag=True,
    help="Disable code syntax highlighting (improves generation speed)",
)
@click.option(
    "--doctor",
    is_flag=True,
    help="Run environment checks and exit",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show full traceback on errors",
)
@click.option(
    "--no-warnings",
    is_flag=True,
    help="Suppress schema version and other warnings",
)
@click.option(
    "--project-dir",
    default=None,
    hidden=True,  # Deprecated, kept for backward compatibility
    help="(Deprecated: use PROJECT_PATH argument instead)",
)
def main(
    input_path: Optional[Path],
    storage_dir: Optional[Path],
    output: Path,
    output_format: str,
    all_projects: bool,
    from_date: Optional[str],
    to_date: Optional[str],
    max_sessions: Optional[int],
    no_individual_sessions: bool,
    no_cache: bool,
    clear_cache: bool,
    clear_output: bool,
    no_open_browser: bool,
    no_todos: bool,
    no_diffs: bool,
    page_size: int,
    no_timeline: bool,
    no_syntax_highlight: bool,
    doctor: bool,
    debug: bool,
    no_warnings: bool,
    project_dir: Optional[str],
) -> None:
    """Generate HTML/Markdown logs from OpenCode local storage.

    \b
    PROJECT_PATH: Optional path to a specific project worktree directory.
                  If not provided, processes all projects by default.

    \b
    Examples:
      # Process all projects and open in browser (default)
      opencode-log

      # Process specific project
      opencode-log /path/to/my-project

      # Process all projects without opening browser
      opencode-log --no-open-browser

      # Generate both HTML and Markdown
      opencode-log --format both

      # Filter by date
      opencode-log --from-date "7 days ago" --to-date "today"

      # Check environment
      opencode-log --doctor
    """
    try:
        # Handle deprecated --project-dir parameter
        if project_dir and not input_path:
            click.echo(
                "Warning: --project-dir is deprecated, use PROJECT_PATH argument instead",
                err=True,
            )
            input_path = Path(project_dir)

        # Default behavior: process all projects if no input path provided
        if input_path is None:
            all_projects = True

        root = storage_dir or _default_storage_dir()

        if not root.exists():
            raise click.ClickException(f"Storage dir not found: {root}")

        if doctor:
            click.echo("[doctor] data path: {}".format(root))
            if root.is_file():
                click.echo("[doctor] using direct db file: {}".format(root))
            else:
                click.echo("[doctor] db path: {}".format(root / "opencode.db"))
                click.echo(
                    "[doctor] db exists: {}".format((root / "opencode.db").exists())
                )
            project_count = len(load_projects(root))
            click.echo(f"[doctor] projects found: {project_count}")
            warnings = get_storage_schema_warnings(root)
            if warnings:
                click.echo("[doctor] warnings:")
                for warning in warnings:
                    click.echo(f"  - {warning}")
            return

        if not no_warnings:
            schema_warnings = get_storage_schema_warnings(root)
            for warning in schema_warnings:
                click.echo(f"Warning: {warning}", err=True)

        # Normalize format parameter
        if output_format == "md":
            output_format = "markdown"

        render_html = output_format in {"html", "both"}
        render_md = output_format in {"markdown", "both"}

        # Handle clear output before processing
        if clear_output:
            if render_html:
                _clear_output_files(output, "html")
            if render_md:
                _clear_output_files(output, "md")

        from_ms = parse_date_to_ms(from_date, end_of_day=False)
        to_ms = parse_date_to_ms(to_date, end_of_day=True)
        if from_date and from_ms is None:
            raise click.ClickException(f"Could not parse --from-date: {from_date}")
        if to_date and to_ms is None:
            raise click.ClickException(f"Could not parse --to-date: {to_date}")

        projects = load_projects(root)
        picked = _pick_projects(projects, input_path, all_projects)
        if not picked:
            raise click.ClickException("No matching projects found")

        cache_manager = (
            None if no_cache else CacheManager(output / ".opencode-log-cache")
        )
        if clear_cache and cache_manager is not None:
            cache_manager.clear()

        sessions_by_project: dict[str, list] = {}
        projects_out = output / "projects"
        projects_out.mkdir(parents=True, exist_ok=True)

        rendered_files = 0
        skipped_files = 0

        for project in picked:
            sessions = load_project_sessions(
                storage_dir=root,
                project_id=project.id,
                from_ms=from_ms,
                to_ms=to_ms,
                max_sessions=max_sessions,
                cache_manager=cache_manager,
                include_todos=not no_todos,
                include_diffs=not no_diffs,
            )
            if not sessions:
                continue

            sessions_by_project[project.id] = sessions
            project_slug = f"{safe_slug(project.display_name)}-{project.id[:8]}"
            project_out = projects_out / project_slug
            project_out.mkdir(parents=True, exist_ok=True)

            if render_html:
                combined_path = project_out / "combined_transcripts.html"
                combined_sig = combined_render_signature(project, sessions)
                combined_key = f"combined:{project.id}"
                should_render_combined = (
                    True
                    if cache_manager is None
                    else cache_manager.should_render(
                        combined_key, combined_sig, combined_path
                    )
                )
                if should_render_combined:
                    render_combined_page(
                        project=project,
                        sessions=sessions,
                        out_file=combined_path,
                        back_link="../../index.html",
                    )
                    rendered_files += 1
                    if cache_manager is not None:
                        cache_manager.mark_rendered(combined_key, combined_sig)
                else:
                    skipped_files += 1

            if render_md:
                combined_md_path = project_out / "combined_transcripts.md"
                combined_md_sig = f"md-combined:{project.id}:{combined_render_signature(project, sessions)}"
                combined_md_key = f"combined-md:{project.id}"
                should_render_combined_md = (
                    True
                    if cache_manager is None
                    else cache_manager.should_render(
                        combined_md_key, combined_md_sig, combined_md_path
                    )
                )
                if should_render_combined_md:
                    render_combined_markdown(
                        project=project, sessions=sessions, out_file=combined_md_path
                    )
                    rendered_files += 1
                    if cache_manager is not None:
                        cache_manager.mark_rendered(combined_md_key, combined_md_sig)
                else:
                    skipped_files += 1

            if not no_individual_sessions:
                session_links = [
                    {
                        "id": s.info.id,
                        "title": s.info.title,
                        "file": f"session-{s.info.id}.html",
                    }
                    for s in sessions
                ]
                for session in sessions:
                    if render_html:
                        session_path = project_out / f"session-{session.info.id}.html"
                        session_sig = session_render_signature(session)
                        session_key = f"session:{session.info.id}"
                        should_render_session_html = (
                            True
                            if cache_manager is None
                            else cache_manager.should_render(
                                session_key, session_sig, session_path
                            )
                        )
                        if should_render_session_html:
                            render_session_page(
                                session=session,
                                out_file=session_path,
                                project_name=project.display_name,
                                back_link="combined_transcripts.html",
                                session_links=session_links,
                            )
                            rendered_files += 1
                            if cache_manager is not None:
                                cache_manager.mark_rendered(session_key, session_sig)
                        else:
                            skipped_files += 1

                    if render_md:
                        session_md_path = project_out / f"session-{session.info.id}.md"
                        md_sig = markdown_render_signature(session)
                        md_key = f"session-md:{session.info.id}"
                        should_render_session_md = (
                            True
                            if cache_manager is None
                            else cache_manager.should_render(
                                md_key, md_sig, session_md_path
                            )
                        )
                        if should_render_session_md:
                            render_session_markdown(
                                session=session,
                                out_file=session_md_path,
                                project_name=project.display_name,
                                session_links=session_links,
                            )
                            rendered_files += 1
                            if cache_manager is not None:
                                cache_manager.mark_rendered(md_key, md_sig)
                        else:
                            skipped_files += 1

                if from_date is None and to_date is None and max_sessions is None:
                    if render_html:
                        keep_html = {f"session-{s.info.id}.html" for s in sessions}
                        for old in project_out.glob("session-*.html"):
                            if old.name not in keep_html:
                                old.unlink(missing_ok=True)
                    if render_md:
                        keep_md = {f"session-{s.info.id}.md" for s in sessions}
                        for old in project_out.glob("session-*.md"):
                            if old.name not in keep_md:
                                old.unlink(missing_ok=True)

        if not sessions_by_project:
            raise click.ClickException("No sessions found after filtering")

        index_path = output / "index.html"
        if render_html:
            idx_sig = index_render_signature(picked, sessions_by_project)
            idx_key = "index"
            should_render_index = (
                True
                if cache_manager is None
                else cache_manager.should_render(idx_key, idx_sig, index_path)
            )
            if should_render_index:
                index_path = render_index_page(output, picked, sessions_by_project)
                rendered_files += 1
                if cache_manager is not None:
                    cache_manager.mark_rendered(idx_key, idx_sig)
            else:
                skipped_files += 1

        if render_md:
            md_index_path = output / "index.md"
            md_index_sig = (
                f"md-index:{index_render_signature(picked, sessions_by_project)}"
            )
            md_index_key = "index-md"
            should_render_md_index = (
                True
                if cache_manager is None
                else cache_manager.should_render(
                    md_index_key, md_index_sig, md_index_path
                )
            )
            if should_render_md_index:
                render_index_markdown(output, picked, sessions_by_project)
                rendered_files += 1
                if cache_manager is not None:
                    cache_manager.mark_rendered(md_index_key, md_index_sig)
            else:
                skipped_files += 1

        if cache_manager is not None:
            cache_manager.save()

        # Cleanup removed projects from output only in full-scan mode
        if (
            from_date is None
            and to_date is None
            and max_sessions is None
            and all_projects
            and input_path is None
        ):
            active_slugs = {
                f"{safe_slug(p.display_name)}-{p.id[:8]}"
                for p in picked
                if p.id in sessions_by_project
            }
            for existing in projects_out.iterdir():
                if existing.is_dir() and existing.name not in active_slugs:
                    shutil.rmtree(existing, ignore_errors=True)

        if render_html:
            click.echo(f"Generated index: {index_path}")
        elif render_md:
            click.echo(f"Generated index: {output / 'index.md'}")
        click.echo(
            f"Rendered files: {rendered_files}, skipped by cache: {skipped_files}"
        )

        # Open browser by default (unless --no-open-browser is specified)
        if render_html and not no_open_browser:
            if all_projects or len(picked) > 1:
                # Multiple projects: open index
                webbrowser.open(index_path.resolve().as_uri())
            else:
                # Single project: open combined transcript
                combined_path = (
                    projects_out
                    / f"{safe_slug(picked[0].display_name)}-{picked[0].id[:8]}"
                    / "combined_transcripts.html"
                )
                if combined_path.exists():
                    webbrowser.open(combined_path.resolve().as_uri())
                else:
                    webbrowser.open(index_path.resolve().as_uri())

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
