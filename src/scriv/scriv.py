"""Central scriv class."""

import datetime
import re
import textwrap
from pathlib import Path

import jinja2

from .config import Config
from .gitinfo import (
    current_branch_name,
    user_nick,
)


class Scriv:
    """TODO: what is this?"""
    def __init__(self, *, config: Config = None):
        if config is None:
            self.config = Config.read()
        else:
            self.config = config

    def new_fragment_path(self) -> Path:
        """
        Return the file path for a new fragment.
        """
        file_name = "{:%Y%m%d_%H%M%S}_{}".format(
            datetime.datetime.now(), user_nick()
        )
        branch_name = current_branch_name()
        if branch_name and branch_name not in self.config.main_branches:
            branch_name = branch_name.rpartition("/")[-1]
            branch_name = re.sub(r"[^a-zA-Z0-9_]", "_", branch_name)
            file_name += "_{}".format(branch_name)
        file_name += ".{}".format(self.config.format)
        file_path = Path(self.config.fragment_directory) / file_name
        return file_path

    def new_fragment_contents(self) -> str:
        """Produce the initial contents of a scriv fragment."""
        return jinja2.Template(
            textwrap.dedent(self.config.new_fragment_template)
        ).render(config=self.config)
