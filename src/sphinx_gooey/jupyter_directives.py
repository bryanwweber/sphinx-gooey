from typing import cast
from docutils.utils import new_document
from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective

from docutils.nodes import Node
from docutils import nodes
from pathlib import Path
from copy import deepcopy
from sphinx.util.logging import getLogger
from myst_nb.sphinx_ import Parser as MystParser


logger = getLogger(__name__)


class JupyterExample(SphinxDirective):
    required_arguments = 1

    def run(self) -> list[Node]:

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
        parser = cast(MystParser, app.registry.create_source_parser(app, "myst-nb"))
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
