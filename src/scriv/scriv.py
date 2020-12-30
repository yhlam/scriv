"""Central scriv class."""

import collections
import datetime
import itertools
import re
import textwrap
from pathlib import Path
from typing import Iterable, List

import attr
import jinja2

from .config import Config
from .format import SectionDict, get_format_tools
from .gitinfo import current_branch_name, user_nick
from .util import order_dict


@attr.s
class Fragment:
    """A changelog fragment."""

    path = attr.ib(type=Path)
    format = attr.ib(type=str, default=None)
    content = attr.ib(type=str, default=None)

    def __attrs_post_init__(
        self,
    ):  # noqa: D105 (Missing docstring in magic method)
        if self.format is None:
            self.format = self.path.suffix.lstrip(".")

    def write(self) -> None:
        """Write the content to the file."""
        self.path.write_text(self.content)

    def read(self) -> None:
        """Read the content of the fragment."""
        self.content = self.path.read_text()


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

    def fragments_to_combine(self) -> List[Fragment]:
        """Get the list of fragments to combine."""
        return [Fragment(path=path) for path in files_to_combine(self.config)]

    def sections_from_fragment(self, fragment: Fragment) -> SectionDict:
        """
        Collect the sections from a fragment.
        """
        fragment.read()
        format_tools = get_format_tools(fragment.format, self.config)
        text = fragment.content.rstrip()
        file_sections = format_tools.parse_text(text)
        return file_sections

    def combine_fragments(self, fragments: Iterable[Fragment]) -> SectionDict:
        """
        Read fragments and produce a combined SectionDict of their contents.
        """
        sections = collections.defaultdict(list)  # type: SectionDict
        for fragment in fragments:
            frag_sections = self.sections_from_fragment(fragment)
            for section, paragraphs in frag_sections.items():
                sections[section].extend(paragraphs)
        sections = order_dict(sections, [None] + self.config.categories)
        return sections


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


def files_to_combine(config: Config) -> List[Path]:
    """
    Find all the fragment file paths to be combined.

    The paths are returned in the order they should be processed.

    """
    paths = sorted(
        itertools.chain.from_iterable(
            [
                Path(config.fragment_directory).glob(pattern)
                for pattern in ["*.rst", "*.md"]
            ]
        )
    )
    return paths
