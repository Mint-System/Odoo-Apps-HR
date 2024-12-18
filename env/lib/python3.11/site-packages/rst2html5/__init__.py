import re
import sys
from collections import OrderedDict
from importlib import metadata
from typing import Any, Dict, List, Optional, Tuple, Union

import docutils
from docutils import nodes, writers
from docutils.frontend import OptionParser, Values
from docutils.nodes import (
    Bibliographic,
    Text,
    TextElement,
    address,
    authors,
    block_quote,
    citation,
    citation_reference,
    classifier,
    colspec,
    comment,
    doctest_block,
    document,
    entry,
    enumerated_list,
    field,
    figure,
    footnote,
    footnote_reference,
    image,
    line,
    line_block,
    literal,
    literal_block,
    math,
    math_block,
    meta,
    option,
    option_argument,
    option_group,
    option_list,
    paragraph,
    problematic,
    raw,
    row,
    rubric,
    section,
    substitution_definition,
    subtitle,
    system_message,
    table,
    thead,
    title,
)
from docutils.nodes import Element as NodeElement
from docutils.transforms import Transform
from docutils.utils.math import pick_math_environment
from genshi.builder import Element, Fragment, tag
from genshi.core import Markup
from genshi.output import XHTMLSerializer

from . import directives, roles  # noqa: F401

__docformat__ = 'reStructuredText'
try:
    __version__ = metadata.version('rst2html5')
except metadata.PackageNotFoundError:
    __version__ = '__development__'

# monkeypatch OptionParser to set 'version'
OptionParser.version_template = (
    f'%prog {__version__} '
    f'(Docutils {docutils.__version__}, '
    f'Python {sys.version.split()[0]}, on {sys.platform.capitalize()})'
)


class FooterToBottom(Transform):

    """
    The doctree must be adjusted before translation begins
    since in-place tree modifications doesn't work.

    The footer must be relocated to the bottom of the
    doctree in order to be translated at the right position.

    .. seealso::

        * http://docutils.sourceforge.net/docs/ref/transforms.html
    """

    default_priority = 850

    def apply(self) -> None:
        for child in self.document.children:
            if isinstance(child, nodes.decoration):
                for footer in child:
                    if isinstance(footer, nodes.footer):
                        child.remove(footer)
                        self.document.append(footer)
                break


class WrapTopTitle(Transform):
    r"""
    If the top element of a document is a title,
    wrap all the document's children within a section.

    For example:

    .. code:: rst

        .. _outer_target:
        .. _inner_target:

        Title 1
        =======

        The targets outer_target_ and inner_target_ point both to Title 1

    The previous snippet should be transformed from:

    .. code:: xml

        <document ids="title-1 inner-target outer-target" \
        names="title\ 1 inner_target outer_target" source="internal_link_2.rst" \
        title="Title 1">
        <title>
            Title 1
        <target refid="outer-target">
        <target refid="inner-target">
        <paragraph>
            The targets
            <reference name="outer_target" refid="outer-target">
                outer_target
             and
            <reference name="inner_target" refid="inner-target">
                inner_target
             point both to Title 1

    into:

    .. code:: xml

        <document source="internal_link_2.rst">
        <section ids="title-1 inner-target outer-target" names="title\ 1 inner_target outer_target">
            <title>
                Title 1
            <paragraph>
                The targets
                <reference name="outer_target" refid="outer-target">
                    outer_target
                 and
                <reference name="inner_target" refid="inner-target">
                    inner_target
                 point both to Title 1
    """

    default_priority = 850

    def apply(self) -> None:
        if 'title' not in self.document:
            return
        section = nodes.section()
        section['ids'] = self.document['ids']
        section['names'] = self.document['names']
        del self.document['ids']
        del self.document['names']
        for child in self.document.children:
            if not (isinstance(child, nodes.target) and child.get('refid') in section['ids']):
                section.children.append(child)
        self.document.children = [section]
        return


def _script_callback_option_parser(
    option: str, opt_str: str, value: str, parser: OptionParser
) -> None:
    """
    Store a script's URL or path along to its attribute 'defer', 'async' or None
    """
    attr = 'defer' in opt_str and 'defer' or 'async' in opt_str and 'async' or None
    if parser.values:
        parser.values.script = parser.values.script or []
        parser.values.script.append((value, attr))


class HTML5Writer(writers.Writer):
    supported = ('html', 'html5', 'html5css3')

    config_section = 'html5writer'
    config_section_dependencies = 'writers'

    # OptParse see https://docs.python.org/2/library/optparse.html
    settings_spec = (
        'rst2html5 Specific Options',
        'For the rst2html5 writer the default tab width value is 4.',
        (
            (
                "Don't indent output",
                ['--no-indent'],
                {
                    'default': 1,
                    'action': 'store_false',
                    'dest': 'indent_output',
                },
            ),
            (
                'Specify a stylesheet URL to be included in the output HTML file. '
                '(This option can be used multiple times)',
                ['--stylesheet'],
                {
                    'metavar': '<URL or path>',
                    'default': None,
                    'action': 'append',
                },
            ),
            (
                'Specify a stylesheet file whose contents will be included into the output HTML file. '
                '(This option can be used multiple times)',
                ['--stylesheet-inline'],
                {
                    'metavar': '<path>',
                    'default': None,
                    'action': 'append',
                },
            ),
            (
                'Specify a script URL to be included in the output HTML file. '
                '(This option can be used multiple times)',
                ['--script'],
                {
                    'metavar': '<URL or path>',
                    'default': None,
                    'dest': 'script',
                    'type': 'string',
                    'action': 'callback',
                    'callback': _script_callback_option_parser,
                },
            ),
            (
                'Specify a script URL with a defer attribute '
                'to be included in the output HTML file. '
                '(This option can be used multiple times)',
                ['--script-defer'],
                {
                    'metavar': '<URL or path>',
                    'dest': 'script',
                    'type': 'string',
                    'action': 'callback',
                    'callback': _script_callback_option_parser,
                },
            ),
            (
                'Specify a script URL with a async attribute '
                'to be included in the output HTML file. '
                '(This option can be used multiple times)',
                ['--script-async'],
                {
                    'metavar': '<URL or path>',
                    'dest': 'script',
                    'type': 'string',
                    'action': 'callback',
                    'callback': _script_callback_option_parser,
                },
            ),
            (
                'Specify a html tag attribute. ' '(This option can be used multiple times)',
                ['--html-tag-attr'],
                {
                    'metavar': '<attribute>',
                    'default': None,
                    'dest': 'html_tag_attr',
                    'action': 'append',
                },
            ),
            (
                'Specify a filename or text to be used as the HTML5 output template. '
                'The template must have the {head} and {body} placeholders. '
                'The "<html{html_attr}>" placeholder is recommended.',
                ['--template'],
                {
                    'metavar': '<filename or text>',
                    'default': None,
                    'dest': 'template',
                    'type': 'string',
                    'action': 'store',
                },
            ),
            (
                'Define a case insensitive identifier to be used with ifdef and ifndef directives. '
                'There is no value associated with an identifier. '
                '(This option can be used multiple times)',
                ['--define'],
                {
                    'metavar': '<identifier>',
                    'dest': 'identifiers',
                    'default': None,
                    'action': 'append',
                },
            ),
        ),
    )

    settings_defaults = {
        'tab_width': 4,
        'syntax_highlight': 'short',
        'field_limit': 0,
        'option_limit': 0,
    }

    def __init__(self) -> None:
        writers.Writer.__init__(self)
        self.translator_class = HTML5Translator

    def translate(self) -> None:
        self.parts['pseudoxml'] = self.document.pformat()  # get pseudoxml before HTML5.translate
        self.document.reporter.debug(
            '%s pseudoxml:\n %s' % (self.__class__.__name__, self.parts['pseudoxml'])
        )
        visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.output
        self.head = visitor.head
        self.body = visitor.body
        self.title = visitor.title
        self.docinfo = visitor.docinfo

    def assemble_parts(self) -> None:
        writers.Writer.assemble_parts(self)
        self.parts['head'] = self.head
        self.parts['body'] = self.body
        self.parts['title'] = self.title
        self.parts['docinfo'] = self.docinfo

    def get_transforms(self) -> List[Transform]:
        return writers.Writer.get_transforms(self) + [
            FooterToBottom,
            WrapTopTitle,
        ]


StackElement = Union[Fragment, Element, str, Markup]


class ElemStack:

    """
    Helper class to handle nested contexts and indentation
    """

    def __init__(self, settings: Values) -> None:
        self.stack: List[List] = []
        self.indent_level = 0
        self.indent_output = settings.indent_output
        self.indent_width = settings.tab_width

    def _indent_elem(self, element: StackElement, indent: bool) -> List:
        result = []
        # Indentation schema:
        #
        #         current position
        #                |
        #                v
        #           <tag>|
        # |   indent   |<elem>
        # |indent-1|</tag>
        #          ^
        #      ends here
        if self.indent_output and indent:
            indentation = '\n' + self.indent_width * self.indent_level * ' '
            result.append(indentation)
        result.append(element)
        if self.indent_output and indent:
            indentation = '\n' + self.indent_width * (self.indent_level - 1) * ' '
            result.append(indentation)
        return result

    def append(self, element: StackElement, indent: bool = True) -> None:
        """
        Append to current element
        """
        self.stack[-1].append(self._indent_elem(element, indent))

    def begin_elem(self) -> None:
        """
        Start a new element context
        """
        self.stack.append([])
        self.indent_level += 1

    def commit_elem(self, elem: Union[Fragment, Element], indent: bool = True) -> None:
        """
        A new element is create by removing its stack to make a tag.
        This tag is pushed back into its parent's stack.
        """
        pop = self.stack.pop()
        elem(*pop)
        self.indent_level -= 1
        self.append(elem, indent)

    def pop(self) -> Element:
        return self.pop_elements(1)[0]

    def pop_elements(self, num_elements: int) -> List[StackElement]:
        assert num_elements > 0
        parent_stack = self.stack[-1]
        result = []
        for x in range(num_elements):
            pop = parent_stack.pop()
            elem = pop[0 if len(pop) == 1 else self.indent_output]
            result.append(elem)
        result.reverse()
        return result


dv = 'default_visit'
dp = 'default_departure'
pass_ = 'no_op'


class HTML5Translator(nodes.NodeVisitor):
    rst_terms = {
        # 'term': ('tag', 'visit_func', 'depart_func', use_term_in_class,
        #          indent_elem)
        # use_term_in_class and indent_elem are optionals.
        # If not given, the default is False, True
        'Text': (None, 'visit_Text', None),
        'abbreviation': ('abbr', dv, dp),
        'acronym': ('abbr', dv, dp),
        'address': (None, 'visit_address', None),
        'admonition': ('aside', 'visit_aside', 'depart_aside', True),
        'attention': ('aside', 'visit_aside', 'depart_aside', True),
        'attribution': ('p', dv, dp, True),
        'author': (None, 'visit_bibliographic_field', None),
        'authors': (None, 'visit_authors', None),
        'block_quote': ('blockquote', 'visit_blockquote', dp),
        'bullet_list': ('ul', dv, dp, False),
        'caption': ('figcaption', dv, dp, False),
        'caution': ('aside', 'visit_aside', 'depart_aside', True),
        'citation': (None, 'visit_citation', 'depart_citation', True),
        'citation_reference': (
            'a',
            'visit_citation_reference',
            'depart_reference',
            True,
            False,
        ),
        'classifier': (None, 'visit_classifier', None),
        'colspec': (None, pass_, 'depart_colspec'),
        'comment': (None, 'visit_comment', None),
        'compound': ('div', dv, dp),
        'contact': (None, 'visit_bibliographic_field', None),
        'container': ('div', dv, dp),
        'copyright': (None, 'visit_bibliographic_field', None),
        'danger': ('aside', 'visit_aside', 'depart_aside', True),
        'date': (None, 'visit_bibliographic_field', None),
        'decoration': (None, 'do_nothing', None),
        'definition': ('dd', dv, dp),
        'definition_list': ('dl', dv, dp),
        'definition_list_item': (None, 'do_nothing', None),
        'description': ('td', dv, dp),
        'docinfo': (None, 'do_nothing', None),
        'doctest_block': (
            'pre',
            'visit_literal_block',
            'depart_literal_block',
            True,
        ),
        'document': (None, 'visit_document', 'depart_document'),
        'emphasis': ('em', dv, dp, False, False),
        'entry': (None, dv, 'depart_entry'),
        'enumerated_list': ('ol', dv, 'depart_enumerated_list'),
        'error': ('aside', 'visit_aside', 'depart_aside', True),
        'field': (None, 'visit_field', None),
        'field_body': (None, 'do_nothing', None),
        'field_list': (None, 'do_nothing', None),
        'field_name': (None, 'do_nothing', None),
        'figure': (None, 'visit_figure', dp),
        'footer': (None, dv, dp),
        'footnote': (None, 'visit_citation', 'depart_citation', True),
        'footnote_reference': (
            'a',
            'visit_citation_reference',
            'depart_reference',
            True,
            False,
        ),
        'generated': (None, 'do_nothing', None),
        'header': (None, dv, dp),
        'hint': ('aside', 'visit_aside', 'depart_aside', True),
        'image': ('img', 'visit_image', 'depart_image'),
        'important': ('aside', 'visit_aside', 'depart_aside', True),
        'inline': ('span', dv, dp, False, False),
        'label': ('th', 'visit_reference', 'depart_label'),
        'legend': ('div', dv, dp, True),
        'line': (None, 'visit_line', None),
        'line_block': ('pre', 'visit_line_block', 'depart_line_block', True),
        'list_item': ('li', dv, dp),
        'literal': ('code', 'visit_literal', 'depart_literal', False, False),
        'literal_block': (
            'pre',
            'visit_literal_block',
            'depart_literal_block',
        ),
        'math': (None, 'visit_math_block', None),
        'math_block': (None, 'visit_math_block', None),
        'meta': (None, 'visit_meta', None),
        'note': ('aside', 'visit_aside', 'depart_aside', True),
        'option': ('kbd', 'visit_option', dp, False, False),
        'option_argument': ('var', 'visit_option_argument', dp, False, False),
        'option_group': ('td', 'visit_option_group', 'depart_option_group'),
        'option_list': (None, 'visit_option_list', 'depart_option_list', True),
        'option_list_item': ('tr', dv, dp),
        'option_string': (None, 'do_nothing', None),
        'organization': (None, 'visit_bibliographic_field', None),
        'paragraph': ('p', 'visit_paragraph', dp),
        'pending': (None, dv, dp),
        'problematic': (
            'a',
            'visit_problematic',
            'depart_reference',
            True,
            False,
        ),
        'raw': (None, 'visit_raw', None),
        'reference': (
            'a',
            'visit_reference',
            'depart_reference',
            False,
            False,
        ),
        'revision': (None, 'visit_bibliographic_field', None),
        'row': ('tr', 'visit_row', 'depart_row'),
        'rubric': ('p', dv, 'depart_rubric', True),
        'section': ('section', 'visit_section', 'depart_section'),
        'sidebar': ('aside', 'visit_aside', 'depart_aside', True),
        'status': (None, 'visit_bibliographic_field', None),
        'strong': (None, dv, dp, False, False),
        'subscript': ('sub', dv, dp, False, False),
        'substitution_definition': (None, 'skip_node', None),
        'substitution_reference': (None, 'skip_node', None),
        'subtitle': (None, 'visit_target', 'depart_subtitle'),
        'superscript': ('sup', dv, dp, False, False),
        'system_message': ('div', 'visit_system_message', dp),
        'table': (None, 'visit_table', 'depart_table'),
        'target': ('a', 'visit_target', 'depart_reference', False, False),
        'tbody': (None, dv, dp),
        'term': ('dt', dv, dp),
        'tgroup': (None, 'do_nothing', None),
        'thead': (None, 'visit_thead', 'depart_thead'),
        'tip': ('aside', 'visit_aside', 'depart_aside', True),
        'title': (None, dv, 'depart_title'),
        'title_reference': ('cite', dv, dp, False, False),
        'topic': ('aside', 'visit_aside', 'depart_aside', True),
        'transition': ('hr', dv, dp),
        'version': (None, 'visit_bibliographic_field', None),
        'warning': ('aside', 'visit_aside', 'depart_aside', True),
    }

    default_template = (
        '<!DOCTYPE html>\n<html{html_attr}>\n' '<head>{head}</head>\n<body>{body}</body>\n</html>'
    )

    def _map_terms_to_functions(self) -> None:
        """
        Map terms to visit and departure functions
        """
        for term, spec in self.rst_terms.items():
            visit_func = spec[1] and getattr(self, str(spec[1]), self.unknown_visit)
            depart_func = spec[2] and getattr(self, str(spec[2]), self.unknown_departure)
            if visit_func:
                setattr(self, 'visit_' + term, visit_func)
            if depart_func:
                setattr(self, 'depart_' + term, depart_func)

    def __init__(self, document: document) -> None:
        nodes.NodeVisitor.__init__(self, document)
        self.heading_level = int(getattr(self.document.settings, 'initial_header_level', 0))
        if self.heading_level > 0:
            self.heading_level -= 1
        self.context = ElemStack(document.settings)
        self.docinfo: Dict = OrderedDict()
        self._parse_params()
        self._map_terms_to_functions()

    def _parse_params(self) -> None:
        self.metatags = [tag.meta(charset=self.document.settings.output_encoding)]
        self.stylesheets = []
        stylesheets = self.document.settings.stylesheet or []
        for href in stylesheets:
            self.stylesheets.append(tag.link(rel='stylesheet', href=href))
        stylesheets_inline = []
        for path in self.document.settings.stylesheet_inline or []:
            with open(path) as f:
                stylesheets_inline.append(f.read())
        if stylesheets_inline:
            self.stylesheets.append(tag.style(Markup(''.join(stylesheets_inline))))
        self.scripts = []
        scripts = self.document.settings.script or []
        for src, attributes in scripts:
            script = tag.script(src=src)
            if attributes:
                script = script(**{attributes: attributes})
            self.scripts.append(script)

    def _get_template(self) -> str:
        template = self.document.settings.template
        if not template:
            return self.default_template
        import os

        if os.path.isfile(template):
            from io import open

            with open(template, 'r', encoding='utf-8') as template_file:
                return template_file.read()
        else:
            return template

    def _get_template_values(self) -> Dict[str, Any]:
        html_attrs = self.document.settings.html_tag_attr
        html_attrs = html_attrs and ' ' + ' '.join(html_attrs) or ''
        head = self.metatags + self.stylesheets + self.scripts
        for key, value in self.docinfo.items():
            head.append(tag.meta(content=value, name=key))
        # indent head
        if self.document.settings.indent_output:
            indent = '\n' + ' ' * self.document.settings.tab_width
            result = []
            for f in head:
                result.append(tag(indent, f))
            result.append('\n')
            head = result
        self.head = ''.join(XHTMLSerializer()(tag(*head)))
        self.body = ''.join(XHTMLSerializer()(tag(*self.context.stack)))
        values = {}
        values['html_attr'] = html_attrs
        values['head'] = self.head
        values['body'] = self.body
        return values

    @property
    def output(self) -> str:
        template = self._get_template()
        values = self._get_template_values()
        return template.format(**values)

    def parse(self, node: NodeElement) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Get tag name, indentantion and correct attributes of a node according
        to its class
        """
        node_class_name = node.__class__.__name__
        spec = self.rst_terms[node_class_name]
        tag_name = str(spec[0] or node_class_name)
        use_name_in_class = len(spec) > 3 and spec[3]
        indent = bool(spec[4]) if len(spec) > 4 else True
        if use_name_in_class:
            node['classes'].insert(0, node_class_name)

        replacements = {
            'refuri': 'href',
            'uri': 'src',
            'refid': 'href',
            'morerows': 'rowspan',
            'morecols': 'colspan',
            'classes': 'class',
            'ids': 'id',
        }
        ignores = (
            'names',
            'dupnames',
            'bullet',
            'enumtype',
            'colwidth',
            'stub',
            'backrefs',
            'auto',
            'anonymous',
        )
        attributes = {}
        for k, v in node.attributes.items():
            if k in ignores or not v:
                continue
            if k in replacements:
                k = replacements[k]
            if isinstance(v, list):
                v = ' '.join(v)
            attributes[k] = v

        return tag_name, indent, attributes

    def once_attr(self, name: str, default: Optional[bool] = None) -> Union[bool, Any]:
        """
        The attribute is used once and then it is deleted
        """
        if hasattr(self, name):
            result = getattr(self, name)
            delattr(self, name)
            return result
        else:
            return default

    def default_visit(self, node: NodeElement) -> None:
        """
        Initiate a new context to store inner HTML5 elements.
        """
        if 'ids' in node and self.once_attr('expand_id_to_anchor', default=True):
            # create an anchor <a id=id></a> on top of the current element
            # for each id found.
            for id in node['ids'][1:]:
                self.context.begin_elem()
                self.context.commit_elem(tag.a(id=id))
            node['ids'] = node['ids'][0:1]
        self.context.begin_elem()

    def default_departure(self, node: NodeElement) -> None:
        """
        Create the node's corresponding HTML5 element and combine it with its
        stored context.
        """
        tag_name, indent, attributes = self.parse(node)
        elem = getattr(tag, tag_name)(**attributes)
        self.context.commit_elem(elem, indent)

    def _compacted_paragraph(self, node: paragraph) -> bool:
        """
        Determine if the <p> tags around paragraph ``node`` can be omitted.
        Based on :func:`docutils.writers.html4css1.HTMLTranslator.should_be_compact_paragraph`
        """

        # extra parenthesis for pep8 alignment conformity
        if (
            isinstance(
                node.parent,
                (
                    nodes.document,
                    nodes.compound,
                    nodes.block_quote,
                    nodes.system_message,
                ),
            )
            or node['classes']
            or 'paragraph' != node.__class__.__name__
        ):
            return False
        # skip label
        first = isinstance(node.parent[0], nodes.label)  # type: ignore
        for child in node.parent.children[first:]:  # type: ignore
            # only first paragraph can be compact
            if isinstance(child, nodes.Invisible):
                continue
            if child is node:
                break
            return False
        if isinstance(node.parent, nodes.list_item):
            # first child of a list_item
            return True
        parent_length = len(
            [n for n in node.parent if not isinstance(n, (nodes.Invisible, nodes.label))]  # type: ignore
        )
        return parent_length == 1

    def visit_paragraph(self, node: paragraph) -> None:
        if self._compacted_paragraph(node):
            raise nodes.SkipDeparture
        self.default_visit(node)

    def visit_Text(self, node: Text) -> None:
        text = node.astext()
        if not getattr(self, 'preserve_space', None):
            text = _strip_spaces(text)
        self.context.append(text, indent=False)
        raise nodes.SkipDeparture

    def visit_section(self, node: section) -> None:
        self.heading_level += 1
        self.default_visit(node)

    def depart_section(self, node: section) -> None:
        self.heading_level -= 1
        self.default_departure(node)

    def depart_title(self, node: title) -> None:
        spec, indent, attr = self.parse(node)
        if isinstance(node.parent, nodes.table):
            elem = tag.caption(**attr)
        else:
            assert self.heading_level >= 0
            if self.heading_level == 0:
                self.heading_level = 1
            if 'href' in attr:
                # backref to toc entry
                del attr['href']
            elem = getattr(tag, 'h' + str(self.heading_level))(**attr)
        self.context.commit_elem(elem, indent)

    def depart_subtitle(self, node: subtitle) -> None:
        # mount the subtitle heading
        subheading_level = getattr(tag, 'h' + str(self.heading_level + 1))
        self.context.commit_elem(subheading_level)
        self.heading_level -= 1

    def depart_enumerated_list(self, node: enumerated_list) -> None:
        """
        Ordered list.
        It may have a preffix and suffix that must be handled by CSS3 and
        javascript to be presented as intended.

        .. seealso::

            * `Automatic numbering with CSS Counters <http://goo.gl/nXq02>`_
            * `How to add brackets to an ordered list? <http://goo.gl/Tdzmf>`_
        """
        if 'enumtype' in node:
            enumtypes = {
                'arabic': '1',
                'loweralpha': 'a',
                'upperalpha': 'A',
                'lowerroman': 'i',
                'upperroman': 'I',
            }
            node['type'] = enumtypes.get(node['enumtype'], '1')
        if node.get('suffix') == '.' and 'preffix' not in node:
            # default suffix doesn't need special treatment
            del node['suffix']
        self.default_departure(node)

    def skip_node(self, node: substitution_definition) -> None:
        """Internal only"""
        raise nodes.SkipNode

    def no_op(self, node: colspec) -> None:
        pass

    def do_nothing(self, node: NodeElement) -> None:
        """
        equivalent to visit: pass and depart: pass
        """
        raise nodes.SkipDeparture

    def visit_classifier(self, node: classifier) -> None:
        """
        Classifier should remain beside the previous element
        """
        term = self.context.pop()
        term(
            ' ',
            tag.span(':', class_='classifier-delimiter'),
            ' ',
            tag.span(node.astext(), class_='classifier'),
        )
        self.context.append(term)
        raise nodes.SkipNode

    #
    # table
    #

    def visit_table(self, node: table) -> None:
        self.th_required = 0
        self.in_thead = False
        self.default_visit(node)

    def depart_table(self, node: table) -> None:
        del self.th_required
        del self.in_thead
        self.default_departure(node)

    def depart_colspec(self, node: colspec) -> None:
        """
        <col /> tags are not generated anymore because they're pretty useless
        since they cannot receive any attribute from a rst table.
        Anyway, there are better ways to apply styles to columns.
        See http://csswizardry.com/demos/zebra-striping/ for example.

        Nevertheless,
        if a colspec node with a "stub" attribute indicates that the column should be a th tag.
        """
        if 'stub' in node:
            self.th_required += 1

    def visit_thead(self, node: thead) -> None:
        self.in_thead = True
        self.default_visit(node)

    def depart_thead(self, node: thead) -> None:
        self.in_thead = False
        self.default_departure(node)

    def visit_row(self, node: row) -> None:
        self.th_available = self.th_required
        self.default_visit(node)

    def depart_row(self, node: row) -> None:
        del self.th_available
        self.default_departure(node)

    def depart_entry(self, node: entry) -> None:
        if self.in_thead or self.th_available:
            name = 'th'
            self.th_available -= 1
        else:
            name = 'td'

        if 'morerows' in node:
            node['morerows'] = node['morerows'] + 1
        if 'morecols' in node:
            node['morecols'] = node['morecols'] + 1

        waste, indent, attr = self.parse(node)
        self.context.commit_elem(getattr(tag, name)(**attr))

    def visit_reference(self, node: TextElement) -> None:
        if 'ids' in node:
            del node['ids']
        self.default_visit(node)

    def depart_reference(self, node: TextElement) -> None:
        if 'name' in node:
            del node['name']
        if 'refid' in node:
            node['refid'] = '#' + node['refid']
        self.default_departure(node)

    def visit_target(self, node: TextElement) -> None:
        if not node.astext():
            raise nodes.SkipNode
        self.expand_id_to_anchor = False
        self.default_visit(node)

    def visit_literal(self, node: literal) -> None:
        self.preserve_space = getattr(self, 'preserve_space', 0) + 1
        self.default_visit(node)

    def depart_literal(self, node: literal) -> None:
        self.preserve_space -= 1
        if self.preserve_space == 0:
            del self.preserve_space
        if node['classes']:
            node['classes'] = node['classes'][-1]
        self.default_departure(node)

    def visit_literal_block(self, node: Union[literal_block, doctest_block]) -> None:
        """
        Translates a code-block/sourcecode or a parsed-literal block.

        Pygments is used for highlighting by the code-block directive.
        See CodeBlock directive source code for more information.
        """
        # see case parsed_literal_as_code_block
        language = None
        if 'classes' in node and 'code' in node['classes']:
            for c in node['classes']:
                if c.startswith('language-'):
                    language = c
                    break
        if language:
            node['classes'].remove('code')
            node['classes'].remove(language)
            node['data-language'] = language[len('language-') : :]

        self.preserve_space = 1
        self.default_visit(node)

    def depart_literal_block(self, node: Union[literal_block, doctest_block]) -> None:
        del self.preserve_space
        self.default_departure(node)

    def visit_math_block(self, node: Union[math, math_block]) -> None:
        """
        Only MathJax support
        """
        math_code = node.astext()
        if isinstance(node, nodes.math):
            template = r'\(%s\)' % math_code
            elem = tag.span(template)
        else:
            math_env = pick_math_environment(math_code)
            if 'align' in math_env:
                template = '\\begin{%s}\n%s\n\\end{%s}' % (
                    math_env,
                    math_code,
                    math_env,
                )
            else:  # equation
                template = r'\(%s\)' % math_code
            elem = tag.div(template)
        node['classes'].insert(0, 'math')
        waste, waste_, attr = self.parse(node)
        elem(**attr)
        self.context.append(elem)
        if not getattr(self, 'already_has_math_script', None):
            src = 'http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'
            self.scripts.append(tag.script(src=src))
            self.already_has_math_script = True
        raise nodes.SkipNode

    def visit_document(self, node: document) -> None:
        if 'title' in node:
            self.metatags.insert(0, tag.title(node['title']))
            self.title = node['title']
        else:
            self.title = ''
        self.default_visit(node)

    def depart_document(self, node: document) -> None:
        self.context.stack = self.context.stack[0]

    def visit_raw(self, node: raw) -> None:
        if 'html' in node.get('format', ''):
            self.context.append(Markup(node.astext()), indent=False)
        raise nodes.SkipNode

    def visit_aside(self, node: NodeElement) -> None:
        self.save_heading_level = self.heading_level
        self.heading_level = 1
        self.default_visit(node)

    def depart_aside(self, node: NodeElement) -> None:
        self.heading_level = self.save_heading_level
        del self.save_heading_level
        if node['classes'] and node['classes'][0].startswith('admonition-'):
            del node['classes'][0]
        self.default_departure(node)

    def depart_rubric(self, node: rubric) -> None:
        node['classes'] = []
        self.default_departure(node)

    def visit_field(self, node: field) -> None:
        self.docinfo[node.children[0].astext()] = _strip_spaces(node.children[1].astext())
        raise nodes.SkipNode

    def visit_bibliographic_field(self, node: Bibliographic) -> None:
        self.docinfo[node.__class__.__name__] = _strip_spaces(node.astext())
        raise nodes.SkipNode

    def visit_address(self, node: address) -> None:
        self.docinfo[node.__class__.__name__] = ', '.join(node.astext().split('\n'))
        raise nodes.SkipNode

    def visit_authors(self, node: authors) -> None:
        self.docinfo[node.__class__.__name__] = '; '.join(node.astext().split())
        raise nodes.SkipNode

    def visit_option_list(self, node: Union[footnote, citation, option_list]) -> None:
        self.context.begin_elem()  # table
        self.context.begin_elem()  # tbody

    def depart_option_list(self, node: Union[footnote, citation, option_list]) -> None:
        self.context.commit_elem(tag.tbody)
        waste, waste_, attr = self.parse(node)
        self.context.commit_elem(tag.table(**attr))

    def visit_citation(self, node: Union[footnote, citation]) -> None:
        self.visit_option_list(node)
        self.context.begin_elem()  # tr

    def depart_citation(self, node: Union[footnote, citation]) -> None:
        # td initiated at depart_label
        self.context.commit_elem(tag.td)
        self.context.commit_elem(tag.tr)
        self.depart_option_list(node)

    def visit_option_group(self, node: option_group) -> None:
        self.option_level = 0
        self.default_visit(node)

    def depart_option_group(self, node: option_group) -> None:
        if (
            self.document.settings.option_limit
            and len(node.astext()) > self.document.settings.option_limit
        ):
            node['morecols'] = 2
            self.default_departure(node)
            self.context.commit_elem(tag.tr)  # closes this tr
            self.context.begin_elem()  # begins another tr
            self.context.append(tag.td)  # empty td due to colspan
        else:
            self.default_departure(node)

    def visit_option(self, node: option) -> None:
        if self.option_level:
            self.context.append(', ', indent=False)
        self.option_level += 1
        self.default_visit(node)

    def visit_option_argument(self, node: option_argument) -> None:
        if 'delimiter' in node:
            self.context.append(node['delimiter'], indent=False)
            del node['delimiter']
        self.default_visit(node)

    def visit_citation_reference(self, node: Union[footnote_reference, citation_reference]) -> None:
        """
        Instead of a typical visit_reference call this def is required to
        remove the backref id that is included but not used in rst2html5.
        """
        self.expand_id_to_anchor = False
        self.default_visit(node)

    def depart_label(self, node: nodes.label) -> None:
        self.default_departure(node)
        self.context.begin_elem()  # next td

    def visit_line(self, node: line) -> None:
        self.line_level = getattr(self, 'line_level', -1) + 1
        if self.line_level:
            tab_width = self.document.settings.tab_width
            separator = '\n' + ' ' * tab_width * (self.line_block_level - 1)
            self.context.append(separator, indent=False)
        raise nodes.SkipDeparture

    def visit_line_block(self, node: line_block) -> None:
        """
        Line blocks use <pre>.
        Lines breaks and spacing are reconstructured based on line_block_level
        """
        self.line_block_level = getattr(self, 'line_block_level', 0) + 1
        if self.line_block_level == 1:
            self.default_visit(node)

    def depart_line_block(self, node: line_block) -> None:
        self.line_block_level -= 1
        if self.line_block_level == 0:
            del self.line_block_level
            del self.line_level
            self.default_departure(node)

    def visit_meta(self, node: meta) -> None:
        waste, waste_, attr = self.parse(node)
        self.metatags.append(tag.meta(**attr))
        raise nodes.SkipNode

    def visit_problematic(self, node: problematic) -> None:
        self.expand_id_to_anchor = False
        if len(node['ids']) > 1:
            node['ids'] = node['ids'][0]
        self.default_visit(node)

    def visit_system_message(self, node: system_message) -> None:
        self.default_visit(node)
        self.context.begin_elem()  # h1
        backrefs = [tag(' ', tag.a(v, href='#' + v)) for v in node['backrefs']]
        node.setdefault('line', '')
        text = 'System Message: {type}/{level} ({source} line ' '{line})'.format(**node.attributes)
        h1 = tag.h1(text, *backrefs)
        self.context.commit_elem(h1)
        node.attributes = {'classes': [], 'ids': node['ids']}

    def visit_figure(self, node: figure) -> None:
        image = node.children[0] if len(node.children) > 0 else None
        caption = node.children[1] if len(node.children) > 1 else None
        legend = node.children[2] if len(node.children) > 2 else None

        # move up the ids of image
        if isinstance(image, nodes.image) and 'ids' in image:
            node['ids'].extend(image['ids'])
            image['ids'] = []

        # group legend's children into caption
        if isinstance(legend, nodes.legend):
            if isinstance(caption.children[0], nodes.Text):
                text = caption.pop().astext()
                paragraph = nodes.paragraph(text=text)
                caption.append(paragraph)
            caption.extend(legend.children)
            node.remove(legend)

        self.default_visit(node)

    def visit_comment(self, node: comment) -> None:
        text = node.astext()
        if text:
            self.context.begin_elem()
            comment = tag(Markup('<!-- '), text, Markup(' -->'))
            self.context.commit_elem(comment)
        raise nodes.SkipNode

    def visit_blockquote(self, node: block_quote) -> None:
        if isinstance(node.parent, nodes.list_item):
            raise nodes.SkipDeparture
        self.default_visit(node)

    def visit_image(self, node: image) -> None:
        def ignore_attr(attr: str) -> None:
            if attr in node:
                del node[attr]
                self.document.reporter.warning(f'Property :{attr}: was ignore for image')

        def check_unit(attr: str) -> None:
            if attr in node:
                value = re.findall(r'^(\d+)(px)?$', node[attr])
                if not value:
                    self.document.reporter.warning(
                        f'Property {attr} must use "px" or no unit at all'
                    )
                else:
                    node[attr] = value[0][0]  # only the number

        ignore_attr('align')
        ignore_attr('scale')
        check_unit('height')
        check_unit('width')
        node.setdefault('alt', '')
        self.default_visit(node)

    def depart_image(self, node: image) -> None:
        tag_name, indent, attributes = self.parse(node)
        attributes.setdefault('alt', '')
        elem = getattr(tag, tag_name)(**attributes)
        self.context.commit_elem(elem, indent)


def _strip_spaces(text: str) -> str:
    return re.sub(r'\s+', ' ', text)
