"""Collecting fragments."""

import datetime
import logging
from pathlib import Path
from typing import Optional

import click
import click_log
import jinja2

from .format import get_format_tools
from .gitinfo import git_add, git_config_bool, git_edit, git_rm
from .scriv import Scriv
from .util import cut_at_line

logger = logging.getLogger()


@click.command()
@click.option(
    "--add/--no-add", default=None, help="'git add' the updated changelog file."
)
@click.option(
    "--edit/--no-edit",
    default=None,
    help="Open the changelog file in your text editor.",
)
@click.option(
    "--keep", is_flag=True, help="Keep the fragment files that are collected."
)
@click.option(
    "--version", default=None, help="The version name to use for this entry."
)
@click_log.simple_verbosity_option(logger)
def collect(
    add: Optional[bool], edit: Optional[bool], keep: bool, version: str
) -> None:
    """
    Collect fragments and produce a combined entry in the CHANGELOG file.
    """
    if add is None:
        add = git_config_bool("scriv.collect.add")
    if edit is None:
        edit = git_config_bool("scriv.collect.edit")

    scriv = Scriv()
    logger.info("Collecting from {}".format(scriv.config.fragment_directory))
    frags = scriv.fragments_to_combine()
    sections = scriv.combine_fragments(frags)

    changelog = Path(scriv.config.output_file)
    newline = ""
    if changelog.exists():
        with changelog.open("r") as f:
            changelog_text = f.read()
            if f.newlines:  # .newlines may be None, str, or tuple
                if isinstance(f.newlines, str):
                    newline = f.newlines
                else:
                    newline = f.newlines[0]
        text_before, text_after = cut_at_line(
            changelog_text, scriv.config.insert_marker
        )
    else:
        text_before = ""
        text_after = ""

    format_tools = get_format_tools(scriv.config.format, scriv.config)
    title_data = {
        "date": datetime.datetime.now(),
        "version": version or scriv.config.version,
    }
    new_title = jinja2.Template(scriv.config.entry_title_template).render(
        config=scriv.config, **title_data
    )
    if new_title.strip():
        new_header = format_tools.format_header(new_title)
    else:
        new_header = ""
    new_text = format_tools.format_sections(sections)
    with changelog.open("w", newline=newline or None) as f:
        f.write(text_before + new_header + new_text + text_after)

    if edit:
        git_edit(changelog)

    if add:
        git_add(changelog)

    if not keep:
        for frag in frags:
            logger.info("Deleting fragment file {!r}".format(str(frag.path)))
            if add:
                git_rm(frag.path)
            else:
                frag.path.unlink()
