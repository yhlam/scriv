"""Central scriv class."""

import datetime
import re
import textwrap
from pathlib import Path

import attr
import jinja2

from .config import Config
from .gitinfo import current_branch_name, user_nick


@attr.s
class Fragment:
    """A changelog fragment."""

    format = attr.ib(type=str)
    path = attr.ib(type=Path)
    content = attr.ib(type=str)

    def write(self) -> None:
        """Write the content to the file."""
        self.path.write_text(self.content)


class Scriv:
    """Public API to the scriv application."""

    def __init__(self, *, config: Config = None):
        """Create a new Scriv."""
        if config is None:
            self.config = Config.read()
        else:
            self.config = config

    def new_fragment(self) -> Fragment:
        """
        Create a new fragment.
        """
        return Fragment(
            format=self.config.format,
            path=new_fragment_path(self.config),
            content=new_fragment_content(self.config),
        )


def new_fragment_path(config: Config) -> Path:
    """
    Return the file path for a new fragment.
    """
    file_name = "{:%Y%m%d_%H%M%S}_{}".format(
        datetime.datetime.now(), user_nick()
    )
    branch_name = current_branch_name()
    if branch_name and branch_name not in config.main_branches:
        branch_name = branch_name.rpartition("/")[-1]
        branch_name = re.sub(r"[^a-zA-Z0-9_]", "_", branch_name)
        file_name += "_{}".format(branch_name)
    file_name += ".{}".format(config.format)
    file_path = Path(config.fragment_directory) / file_name
    return file_path


def new_fragment_content(config: Config) -> str:
    """Produce the initial content of a scriv fragment."""
    return jinja2.Template(
        textwrap.dedent(config.new_fragment_template)
    ).render(config=config)
