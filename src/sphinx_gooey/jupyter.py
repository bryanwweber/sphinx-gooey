try:
    import myst_nb  # noqa: F401

except ImportError as e:
    from sphinx.errors import SphinxError

    raise SphinxError(
        "The MystNB extension is not available, so we cannot parse "
        "Jupyter Notebook examples"
    ) from e

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import cast

import nbformat as nbf
from docutils import nodes
from docutils.nodes import Node
from docutils.utils import new_document
from myst_nb.sphinx_ import Parser as MystParser
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.logging import getLogger

from .python import Example

logger = getLogger(__name__)


class JupyterExampleDirective(SphinxDirective):
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

        def doc2path(docname: str, *args: tuple, **kwargs: dict) -> str:
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


@dataclass
class JupyterExample(Example):
    def __post_init__(self) -> None:
        super().__post_init__()
        document = nbf.reads(self.path.read_text(), nbf.current_nbformat)
        summary: list[str] = []
        title: str = ""
        for cell in document.cells:
            if cell.cell_type != "markdown":
                continue
            for line in cell.source.splitlines():
                if summary and title and not line:
                    break
                if not title and line.startswith("#"):
                    title = line.replace("#", "")
                else:
                    summary.append(line)
            break
        self.summary = " ".join(summary)
        self.name = title


def md_generator(ext: str, app: Sphinx, source_folder: Path) -> list[JupyterExample]:
    examples: list[JupyterExample] = []
    for ff in source_folder.rglob(ext):
        pth = ff.relative_to(app.srcdir)
        if " " in str(pth):
            logger.warning(
                f"The example '{pth!s}' has a space in the "
                "pathname which is not yet supported."
            )
            continue
        example = JupyterExample(ff, source_folder)
        examples.append(example)
        md_file = ff.with_suffix(".md")
        md_file.write_text(
            dedent(
                f"""\
                ---
                orphan: true
                ---
                ({example.reference})=
                # {example.path.name}

                :::{{jupyter-example}} {ff.name}
                :::
                """
            )
        )
    return examples
