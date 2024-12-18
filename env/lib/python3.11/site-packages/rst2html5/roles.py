import re
from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst.roles import register_local_role
from docutils.parsers.rst.states import Inliner

# borrowed from Pelican
# https://github.com/getpelican/pelican/blob/d43b786b300358e8a4cbae4afc4052199a7af762/pelican/rstdirectives.py#L76


class abbreviation(nodes.Inline, nodes.TextElement):
    pass


_abbr_re = re.compile(r'\((.*)\)$', re.DOTALL)


def abbr_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner,
    options: Dict[str, Any] = {},
    content: List[str] = [],
) -> Tuple[List[Any], List[Any]]:
    m = _abbr_re.search(text)
    if m is None:
        return [abbreviation(text, text)], []
    abbr = text[: m.start()].strip()
    title = m.group(1)
    return [abbreviation(abbr, abbr, title=title)], []


register_local_role('abbr', abbr_role)
