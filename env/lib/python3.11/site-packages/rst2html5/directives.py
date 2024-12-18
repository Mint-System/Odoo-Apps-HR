import re
from hashlib import md5
from typing import Any, Dict, List, Union

from docutils import nodes
from docutils.nodes import Element, literal_block, table
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives import register_directive
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name


def pygmentize(code: str, language: str, **kwargs: Any) -> str:
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter(**kwargs)
    return highlight(code, lexer, formatter)


#
# The functions below were borrowed from Sphinx to avoid direct dependency to its code
#


def parselinenos(spec: str, total: int) -> List[int]:
    """
    Parse a line number spec (such as "1,2,4-6") and return a list of wanted line numbers.

    copied from sphinx.util import parselinenos
    """
    items = list()
    parts = spec.split(',')
    for part in parts:
        try:
            begend = part.strip().split('-')
            if len(begend) > 2:
                raise ValueError
            if len(begend) == 1:
                items.append(int(begend[0]) - 1)
            else:
                start = (begend[0] == '') and 0 or int(begend[0]) - 1
                end = (begend[1] == '') and total or int(begend[1])
                items.extend(range(start, end))
        except Exception:
            raise ValueError('invalid line number spec: %r' % spec)
    return items


class CodeBlock(Directive):
    """
    Directive for a code block with special highlighting or line numbering
    settings.

    Pygments is used for highlighting.
    However, its highlight output is cluttered and thus rst2html5 cleans it up to a more HTML5 style:

    * It uses 'data-language' attributes instead of attributes such as class="sourcecode" or class="code language".
      Thus, these code-block elements should be addressed in CSS3 using '[data-language]', 'pre[data-language]'
      or 'table[data-language]' selectors.
    * Whenever :number-lines: is used, the highlighting will use table and lineanchors.
    * Lineanchors use :name: parameter if given or else a MD5 hash code.
    * Highlighting without line numbering has the following structure::

        <pre id="name" data-language="language">...</pre>

    * Highlighting with line numbering has the following structure::

        <table id="name_or_hash" data-language="language">
            <tr>
                <td class="linenos">
                    <pre>...</pre>
                </td>
                <td class="code">
                    <pre>...</pre>
                </td>
            </tr>
        </table>
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'class': directives.class_option,
        'emphasize-lines': directives.unchanged_required,
        'name': directives.unchanged,
        'number-lines': directives.unchanged,  # integer or None
    }

    def run(self) -> List[Element]:
        self.assert_has_content()

        language = self.arguments[0]
        code = '\n'.join(self.content)
        pygmentize_args: Dict[str, Any] = {}
        if self.options.get('number-lines', None):
            pygmentize_args['linenostart'] = int(self.options['number-lines'])
        pygmentize_args['linenos'] = 'number-lines' in self.options and 'table'
        node = nodes.table() if pygmentize_args['linenos'] else nodes.literal_block()
        node['classes'] = self.options.get('class', [])
        node.attributes['data-language'] = language
        self.add_name(node)
        set_source_info(self, node)
        if pygmentize_args['linenos']:
            anchor_id = node['ids'][-1] if node['ids'] else md5(code.encode('utf-8')).hexdigest()
            pygmentize_args['lineanchors'] = anchor_id
            pygmentize_args['anchorlinenos'] = True
        linespec = self.options.get('emphasize-lines')
        if linespec:
            try:
                nlines = len(self.content)
                pygmentize_args['hl_lines'] = [x + 1 for x in parselinenos(linespec, nlines)]
            except ValueError as err:
                document = self.state.document
                return [document.reporter.warning(str(err), line=self.lineno)]

        output = pygmentize(code, language, **pygmentize_args)
        # remove empty span included by Pygments
        # See:
        # https://bitbucket.org/birkenfeld/pygments-main/issues/1254/empty-at-the-begining-of-the-highlight
        output = output.replace('<span></span>', '')
        pre = re.findall('<pre.*?>(.*?)\n*</pre>', output, re.DOTALL)
        if len(pre) == 1:
            node += nodes.raw(pre[0], pre[0], format='html')
        else:  # pygments returned a table
            row = nodes.row()
            node += row
            linenos_cell = nodes.entry(classes=['linenos'])
            linenos_cell += nodes.literal_block('', '', nodes.raw(pre[0], pre[0], format='html'))
            code_cell = nodes.entry(classes=['code'])
            code_cell += nodes.literal_block('', '', nodes.raw(pre[1], pre[1], format='html'))
            row += linenos_cell
            row += code_cell

        return [node]


def set_source_info(directive: CodeBlock, node: Union[literal_block, table]) -> None:
    """
    copied from sphinx.util.nodes import set_source_info
    """
    node.source, node.line = directive.state_machine.get_source_and_line(directive.lineno)


class Define(Directive):
    """
    Defines an identifier to be checked by directive ifdef and ifndef.
    Identifiers are case insensitive.
    More than one identifier can be defined at once. Example::

        .. define:: one
        .. define:: two three four

    """

    has_content = False
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> List[Element]:
        if not self.state.document.settings.identifiers:
            identifiers = self.state.document.settings.identifiers = []
        else:
            identifiers = self.state.document.settings.identifiers
        arguments = self.arguments[0].lower().split()
        for identifier in arguments:
            identifier = identifier.lower()
            if identifier not in identifiers:
                identifiers.append(identifier)
        return []


class Undefine(Directive):
    """
    Undefine an identifier. Example::

        .. undef:: one
        .. undef:: one two three four

    """

    has_content = False
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> List[Element]:
        identifiers = self.state.document.settings.identifiers or []
        arguments = self.arguments[0].lower().split()
        for identifier in arguments:
            identifier = identifier.lower()
            if identifier in identifiers:
                identifiers.remove(identifier)
        return []


def _logical_operator(argument: str) -> str:
    return directives.choice(argument, ['and', 'or'])


class IfDef(Directive):
    """
    Include content only if the identifier passed as argument is defined.
    If more than one identified is passed,
    there must be an option to identify which logical operation is to be used:
    'and' or 'or'.  Example::

        .. ifdef:: x y z
            :operator: or

            some content...

    'some content...' only will be included if x or y or z is defined.
    """

    has_content = True
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        'operator': _logical_operator,
    }

    def check(self) -> bool:
        self.assert_has_content()
        identifiers = self.state.document.settings.identifiers or []
        arguments = self.arguments[0].lower().split()
        if len(arguments) == 1:
            identifier = arguments[0]
            show_content = identifier in identifiers
        else:
            if 'operator' not in self.options:
                raise self.error(
                    'You must define an operator when more than one '
                    'identifier is passed as argument.'
                )
            operator = self.options['operator']
            operation = {
                'and': (lambda x, y: x and y),
                'or': (lambda x, y: x or y),
            }
            show_content = operator == 'and'
            for identifier in arguments:
                show_content = operation[operator](show_content, identifier in identifiers)
        return show_content

    def run(self) -> List[Element]:
        if self.check():
            # see Include Directive at docutils/parsers/rst/directives/misc.py
            lines = self.content.data
            source = self.content.source(0)
            self.state_machine.insert_input(lines, source)
        return []


class IfNDef(IfDef):
    """
    Include content only if the identifier passed as argument is not defined.
    See IfDef directive for options
    """

    def check(self) -> bool:
        return not IfDef.check(self)


class StyleSheet(Directive):
    """
    Specify in a restructured text a stylesheet URL or path to be included in the output HTML file.
    """

    has_content = False
    required_arguments = 1
    option_spec = {
        'inline': directives.unchanged,
    }

    def run(self) -> List[Element]:
        settings = self.state.document.settings
        if 'inline' not in self.options:
            stylesheet = settings.stylesheet = settings.stylesheet or []
        else:
            stylesheet = settings.stylesheet_inline = settings.stylesheet_inline or []
        stylesheet.append(self.arguments[0])
        return []


class Script(Directive):
    """
    Specify in a restructured text a script URL or path to be included in the output HTML file.
    """

    has_content = False
    required_arguments = 1
    option_spec = {
        'defer': directives.unchanged,
        'async': directives.unchanged,
    }

    def run(self) -> List[Element]:
        attr = 'defer' in self.options and 'defer' or 'async' in self.options and 'async' or None
        settings = self.state.document.settings
        settings.script = settings.script or []
        settings.script.append((self.arguments[0], attr))
        return []


class Template(Directive):
    """
    Specify in a restructured text a template URL or path to be included in the output HTML file.

    Usage:

    .. template:: <filename>

    or

    .. template::

        <content>

    """

    has_content = True

    def run(self) -> List[Element]:
        settings = self.state.document.settings
        settings.template = len(self.arguments) and self.arguments[0] or '\n'.join(self.content)
        return []


register_directive('code-block', CodeBlock)
register_directive('code', CodeBlock)
register_directive('sourcecode', CodeBlock)
register_directive('define', Define)
register_directive('undef', Undefine)
register_directive('undefine', Undefine)
register_directive('ifdef', IfDef)
register_directive('ifndef', IfNDef)
register_directive('stylesheet', StyleSheet)
register_directive('script', Script)
register_directive('template', Template)
