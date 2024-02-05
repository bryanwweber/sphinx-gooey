try:
    import myst_nb  # noqa: F401

except ImportError as e:
    from sphinx.errors import SphinxError

    raise SphinxError(
        "The MystNB extension is not available, so we cannot parse "
        "Jupyter Notebook examples"
    ) from e

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from typing import cast

import nbformat as nbf
from docutils import nodes
from docutils.nodes import Node
from docutils.utils import new_document
from jupytext.myst import notebook_to_myst
from myst_nb.sphinx_ import Parser as MystParser
from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util.logging import getLogger

from .python import ONE_CARD, Example

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

        # def doc2path(docname: str, *args: tuple, **kwargs: dict) -> str:
        #     """Remove the .md suffix from the doc2path return value. It gets added
        #     automatically by the environment, but since we want to execute the actual
        #     ipynb file on disk, we need to strip it off.
        #     """
        #     pth = app.project.doc2path(docname, *args, **kwargs)  # type: ignore
        #     return pth.removesuffix(".md")

        parser.env.temp_data["docname"] = str(rel_ipynb)
        # parser.env.doc2path = doc2path
        parser.parse(abs_ipynb.read_text(), doc)
        logger.info(doc.children)
        return doc.children


@dataclass
class JupyterExample(Example):
    def __post_init__(self) -> None:
        super().__post_init__()
        document = nbf.reads(self.source_path.read_text(), nbf.current_nbformat)
        summary: list[str] = []
        title: str = ""
        for cell in document.cells:
            if cell.cell_type != "markdown":
                continue
            for line in cell.source.splitlines():
                if summary and title and not line:
                    break
                if not title and line.startswith("#"):
                    title = line.removeprefix("# ")
                else:
                    summary.append(line)
            break
        self.summary = " ".join(summary)
        self.name = title


def md_generator(source_folder: Path, target_folder: Path, config: dict) -> None:
    examples = file_generator(source_folder, target_folder)

    category_block = "::::{{grid}} 1 1 3 3\n{content}\n::::\n"
    block_text = []
    categories = config.get("categories", {})
    for category, these_examples in examples.items():
        if category:
            if category in categories:
                category = categories[category]
            block_text.append(f"## {category}\n")
        block_content = "\n".join(
            [
                ONE_CARD.format(
                    name=example.name,
                    summary=example.summary,
                    reference=example.name.lower().replace(" ", "-"),
                )
                for example in these_examples
            ]
        )
        block_text.extend(category_block.format(content=block_content).splitlines())

    source_index = source_folder / "index.md"
    target_index = target_folder / "index.md"
    if source_index.is_file():
        copy2(source_index, target_index)
        mode = "a"
    else:
        target_index.touch()
        mode = "w"
    with target_index.open(mode) as fp:
        if mode == "w":
            fp.write(f"# {source_folder.name}\n")
        fp.write("\n")
        fp.write("\n".join(block_text))


def file_generator(
    source_folder: Path, target_folder: Path
) -> dict[str, list[JupyterExample]]:
    examples: dict[str, list[JupyterExample]] = defaultdict(list)
    ext = "*.ipynb"
    logger.info("Source folder for Jupyter: %s", source_folder)
    for ff in source_folder.rglob(ext):
        example_file = ff.relative_to(source_folder)
        if " " in str(example_file):
            logger.warning(
                f"The example '{example_file!s}' has a space in the "
                "pathname which is not yet supported."
            )
            continue
        target_file = (target_folder / example_file).with_suffix(".md")
        logger.info(target_file)
        target_file.parent.mkdir(exist_ok=True, parents=True)
        example = JupyterExample(ff, source_folder, target_file)
        examples[example.category].append(example)
        converted_notebook = notebook_to_myst(
            nbf.reads(ff.read_text(), nbf.current_nbformat)
        ).splitlines()
        converted_notebook.insert(1, "orphan: true\nfile_format: mystnb")
        target_file.write_text("\n".join(converted_notebook))
    return examples
