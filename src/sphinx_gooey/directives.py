from textwrap import dedent
from docutils.nodes import Node
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import explicit_title_re, nested_parse_with_titles
from collections import defaultdict

from sphinx.util.logging import getLogger


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
    """Given an example language, generate MyST markdown for the index page
    and each example page. Each example page has the code formatted with
    Pygments, plus a download link for the actual file itself.
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
