from __future__ import annotations
import click
import core.paper_manager as pm


@click.command(name="use")
@click.argument("name")
def use_paper(name: str) -> None:
    """Activate an existing paper."""
    try:
        pm.activate_paper(name)
        click.echo(f"Activated: {name}")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@click.command(name="new")
@click.argument("name")
@click.option("--title", required=True, help="Full paper title")
def new_paper(name: str, title: str) -> None:
    """Create a new paper and activate it."""
    try:
        pm.create_paper(name, title)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    pm.activate_paper(name)
    click.echo(f"Created and activated: {name}")
    click.echo(f"Edit {pm.PAPERS_DIR / name / 'paper.yaml'} to configure sections.")


@click.command(name="list")
def list_papers_cmd() -> None:
    """List all available papers."""
    active = pm.get_active_paper_name()
    papers = pm.list_papers()
    if not papers:
        click.echo("No papers found. Create one with: paper new <name> --title '...'")
        return
    for name in papers:
        try:
            cfg = pm.load_paper_yaml(name)
            label = cfg.get("title", "")
        except ValueError:
            label = "(unreadable paper.yaml)"
        marker = "* " if name == active else "  "
        click.echo(f"{marker}{name} — {label}")
