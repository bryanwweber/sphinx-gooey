import ast
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from textwrap import dedent

from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.logging import getLogger

from .directives import ExampleGallery

logger = getLogger(__name__)


@dataclass
class Example:
    path: Path
    source_folder: Path
    name: str = ""
    reference: str = ""
    summary: str = ""
    category: str = ""

    def __post_init__(self):
        self.name = self.path.name
        has_subdir = len(self.path.relative_to(self.source_folder.parent).parts) > 2
        if has_subdir:
            self.reference = f"{self.path.parts[-2]}-{self.path.stem}"
            self.category = self.path.parts[-2]
        else:
            self.reference = self.path.stem

        self.reference = self.reference.replace("_", "-").replace(" ", "")

        mod = ast.parse(self.path.read_bytes())
        doc = ""
        for node in mod.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                doc = node.value.s.strip().split("\n\n")[0].strip()
                if not doc.endswith("."):
                    doc += "."
                break
        self.summary = doc


def generate_example_md(app: Sphinx, config):
    """
    The extension configuration needs to list the source files folder and file
    extensions. This function will generate ``<filename>.md`` files for each example
    file that is found in a recursive search of the source folder. This may use a
    custom template for each example.

    To use the extension, the user creates an ``index.md`` file that uses the
    ``examples-gallery`` directive somewhere in the file. That directive takes one
    required argument, which is a ``name`` of the set of examples. The ``name`` must be
    configured in the ``conf.py`` file along with the source folder and file
    extensions.

    The usage would look like:

    .. code-block:: markdown

       :::{example-gallery} python
       :::

    The directive is replaced by a set of cards linking to the rendered source code of
    the example and each card contains the description of the example. The gallery is
    automatically subdivided by subfolder in the source location.
    """

    def generic(extension: str, app: Sphinx, source_folder: Path) -> list[Example]:
        examples = []
        for ff in source_folder.rglob(extension):
            pth = ff.relative_to(app.srcdir)
            if " " in str(pth):
                logger.warning(
                    f"The example '{pth!s}' has a space in the "
                    "pathname which is not yet supported."
                )
                continue
            example = Example(ff, source_folder)
            examples.append(example)
            md_file = ff.with_suffix(".md")
            md_file.write_text(
                dedent(
                    f"""\
                    ---
                    orphan: true
                    ---
                    ({example.reference})=
                    # {example.name}

                    [**Source**]({ff.name})

                    :::{{literalinclude}} {ff.name}
                    :::
                    """
                )
            )
        return examples

    generators = app.config.sphinx_gooey_conf.pop("generators")
    for name, values in app.config.sphinx_gooey_conf.items():
        source_folder = Path(app.srcdir) / values["source"]
        if not source_folder.is_dir():
            raise ValueError(
                f"Source folder for examples must exist: '{source_folder!s}'"
            )
        examples = []
        for extension in values["file_ext"]:
            if "ipynb" in extension:
                from .jupyter import JupyterExampleDirective

                app.add_directive("jupyter-example", JupyterExampleDirective)
                jupyter = generators["jupyter"].load()
                examples.extend(jupyter(extension, app, source_folder))
            else:
                examples.extend(generic(extension, app, source_folder))
        references = set(e.reference for e in examples)
        if len(references) != len(examples):
            logger.error("There are duplicate path names in the set of examples")

        app.config.sphinx_gooey_conf[name]["examples"] = examples


def load_generator_entry_points(app: Sphinx, config):
    app.config.sphinx_gooey_conf["generators"] = entry_points(
        group="sphinx_gooey.generators"
    )


def setup(app: Sphinx):
    """Install the extension into the Sphinx ``app``."""

    app.add_config_value("sphinx_gooey_conf", {}, "html")
    app.add_directive("example-gallery", ExampleGallery)

    try:
        app.setup_extension("myst_nb")
    except ExtensionError:
        app.setup_extension("myst_parser")
    app.setup_extension("sphinx_design")

    app.connect("config-inited", generate_example_md, priority=502)
    app.connect("config-inited", load_generator_entry_points, priority=501)
    logger.info("Set up sphinx_gooey!")
