import click
from commands.research import research
from commands.write import write
from commands.cite import cite
from commands.build import build
from commands.build_lv import build_lv
from commands.improve import improve
from commands.improve_all import improve_all
from commands.summary import summary
from commands.manage import use_paper, new_paper, list_papers_cmd
from commands.generate_tests import generate_tests


@click.group()
def cli() -> None:
    """Paper CLI — qualification paper automation."""


cli.add_command(research)
cli.add_command(write)
cli.add_command(cite)
cli.add_command(build)
cli.add_command(build_lv)
cli.add_command(improve)
cli.add_command(improve_all)
cli.add_command(summary)
cli.add_command(use_paper)
cli.add_command(new_paper)
cli.add_command(list_papers_cmd)
cli.add_command(generate_tests)

if __name__ == "__main__":
    cli()
