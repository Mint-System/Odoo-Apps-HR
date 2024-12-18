"""
This file fixes the conflict between docutils and rst2html5 scripts.
See the section "Workaround to Conflicts with Docutils" on docs/design_notes.rst
for more information.
"""

import sys
from pathlib import Path

from docutils.core import default_description, publish_cmdline

# inserts <venv>/lib/<python_version>/site-packages before <venv>/bin in sys.path
# so that ``from rst2html5 ...`` reaches <venv>/lib/<python_version>/site-packages/rst2html5
# instead of docutils' <venv>/bin/rst2html5.py
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from rst2html5 import HTML5Writer  # noqa E402


def main() -> None:
    description = (
        'Generates (X)HTML5 documents from standalone reStructuredText sources.'
        + default_description
    )
    publish_cmdline(writer=HTML5Writer(), description=description)
