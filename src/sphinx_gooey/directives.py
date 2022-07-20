from contextlib import contextmanager
from textwrap import dedent
from typing import TYPE_CHECKING, Generator, cast
from docutils.nodes import Node
from docutils import nodes
from docutils.utils import new_document
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import explicit_title_re, nested_parse_with_titles
from sphinx import addnodes
from collections import defaultdict
from pathlib import Path
from copy import deepcopy

from sphinx.util.logging import getLogger

if TYPE_CHECKING:
    try:
        from myst_nb.sphinx_ import Parser as MystParser
    except ImportError:
        pass

logger = getLogger(__name__)

ONE_CARD = dedent(
    """\
    :::{{grid-item-card}} {name}
    :link: {reference}
    :link-type: ref

    {summary}
    :::
    """
)


class ExampleGallery(SphinxDirective):
    """Given an example language and a path, generate MyST markdown for the index page
    and each example page. Each example page should have the code formatted with
    Pygments, plus a download link for the actual file itself.

    Need to decide between two ways to go forward:

    1. Write the reST/MyST for the grid markup and use ``self.state.nested_parse`` to
       generate the docutils nodes
    2. Instantiate the GridDirective/GridCardItemDirective classes and run their
       ``run()`` methods. The tricky bit here is that the ``GridDirective`` requires
       content to be present in the directive, and I'm not sure how to fake that, or
       even if it makes sense to fake that. For example, the benefit of using markup
       is that the line numbers can be maintained for error output. Another advantage
       is that it's less dependent on the specific code structure in sphinx-design.
       The advantage is that I don't have to write Python string reST markup (blech).
    3. Use ``create_component`` and apply the same style classses as ``sphinx-design``
       uses. Also fragile but maybe less so because it only depends on Bootstrap
    """

    required_arguments = 1
    has_content = True

    def run(self) -> list[Node]:
        if self.arguments[0] not in self.config.sphinx_gooey_conf:
            raise self.error(f"There are no {self.arguments[0]!r} examples.")

        self.examples = defaultdict(list)
        for example in self.config.sphinx_gooey_conf.get(self.arguments[0])["examples"]:
            self.examples[example.category].append(example)

        if not self.content:
            content = self.examples.keys()
        else:
            content = self.content

        categories = {}
        for entry in content:
            explicit = explicit_title_re.match(entry)
            if explicit:
                ref = explicit.group(2)
                if ref == "self":
                    ref = ""
                title = explicit.group(1)
            elif entry == "self":
                ref = title = ""
            else:
                ref = title = entry

            categories[ref] = title

        unknown_category = set(categories.keys()) - set(self.examples.keys())
        if unknown_category:
            raise self.error(
                f"Unknown example category: '{list(categories.keys())}'; '{list(self.examples.keys())}'"
            )

        category_block = "::::{{grid}} 3\n{content}\n::::"
        block_text = []
        for category, title in categories.items():
            block_text.append(f"## {title}")
            examples = self.examples[category]
            content = "\n".join(
                [
                    ONE_CARD.format(
                        name=example.name,
                        summary=example.summary,
                        reference=example.reference,
                    )
                    for example in examples
                ]
            )
            block_text.extend(category_block.format(content=content).splitlines())

        # Empty node so we can return its children, which are added by the nested_parse
        # method.
        node = nodes.section()
        nested_parse_with_titles(self.state, block_text, node)
        return node.children


@contextmanager
def switch_source_input(state, parser, content) -> Generator[None, None, None]:
    from myst_parser.mocking import MockStateMachine

    try:
        get_source_and_line = state.memo.reporter.get_source_and_line
        state_machine = MockStateMachine(
            renderer=state.document.attributes["nb_renderer"], lineno=0
        )
        state_machine.input_lines = content
        state.memo.reporter.get_source_and_line = state_machine.get_source_and_line

        yield
    finally:
        state.memo.reporter.get_source_and_line = get_source_and_line  # type: ignore


class JupyterExample(SphinxDirective):
    required_arguments = 1
    option_spec = {
        "nb_execution_mode": directives.unchanged,
        "embed_stylesheet": directives.unchanged,
    }

    def run(self) -> list[Node]:
        # Import here to avoid a hard dependency on nbformat
        import nbformat as nbf

        doc = new_document("", self.state.document.settings)
        # Two-element tuple, the first is the file relative to the srcdir, the second
        # is the absolute path to the file
        current_ipynb = self.env.relfn2path(self.arguments[0], self.env.docname)
        rel_ipynb = Path(current_ipynb[0])
        abs_ipynb = Path(current_ipynb[1])
        self.env.note_dependency(str(rel_ipynb))

        para = nodes.paragraph()
        doc.append(para)
        wrap_node = addnodes.download_reference(
            refdoc=self.env.docname,
            reftarget=rel_ipynb.name,
            reftype="myst",
            refdomain=None,
            refexplicit=True,
            refwarn=False,
        )
        para.append(wrap_node)
        inner_node = nodes.inline("", "", classes=["xref", "download", "myst"])
        wrap_node.append(inner_node)
        strong_node = nodes.strong()
        inner_node.append(strong_node)
        strong_node.append(nodes.Text("Source"))

        app = self.env.app
        parser = cast("MystParser", app.registry.create_source_parser(app, "myst-nb"))
        parser.env = deepcopy(parser.env)

        def doc2path(docname: str, *args, **kwargs):
            """Remove the .md suffix from the doc2path return value. It gets added
            automatically by the environment, but since we want to execute the actual
            ipynb file on disk, we need to strip it off.
            """
            pth = app.project.doc2path(docname, *args, **kwargs)  # type: ignore
            return pth.removesuffix(".md")

        parser.env.temp_data["docname"] = str(rel_ipynb)
        parser.env.doc2path = doc2path
        parser.parse(abs_ipynb.read_text(), doc)
        return doc.children
