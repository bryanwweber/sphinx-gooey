from importlib.metadata import entry_points
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config as SphinxConfig
from sphinx.environment import Environment
from sphinx.errors import ExtensionError
from sphinx.util.logging import getLogger

from .directives import ExampleGallery

logger = getLogger(__name__)


def generate_example_md(app: Sphinx) -> None:
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

    # Ignore the complaint here that BuildEnvironment has no attribute
    # sphinx_gooey_generators. We could define a type class just for this case but that
    # seems like overkill.
    generators = app.env.sphinx_gooey_generators  # type: ignore
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
            elif "py" in extension:
                python = generators["python"].load()
                examples.extend(python(extension, app, source_folder))
            else:
                default = generators["default"].load()
                examples.extend(default(extension, app, source_folder))
        references = set(e.reference for e in examples)
        if len(references) != len(examples):
            logger.error(
                "There are duplicate path names in the set of examples: %r", references
            )

        app.config.sphinx_gooey_conf[name]["examples"] = examples


def ignore_example_files(app: Sphinx, config: SphinxConfig) -> None:
    filetypes = {".py": "python", ".ipynb": "notebook", ".h": "cxx", ".cpp": "cxx"}
    for values in config.sphinx_gooey_conf.values():
        for extension in values["file_ext"]:
            app.add_source_suffix(extension, filetypes[extension], override=True)
            # app.add_source_parser(parsers[extension], override=True)


def load_generator_entry_points(app: Sphinx) -> None:
    # Ignore the complaint here that BuildEnvironment has no attribute
    # sphinx_gooey_generators. We could define a type class just for this case but that
    # seems like overkill.
    app.env.sphinx_gooey_generators = entry_points(group="sphinx_gooey.generators")  # type: ignore # noqa: E501


def add_fake_files(
    app: Sphinx, env: None, added: None, changed: None, removed: None
) -> list[str]:
    logger.info("Added: %r\nChanged: %r\nRemoved: %r", added, changed, removed)
    return ["docname-1"]


def env_before_read_docs(app: Sphinx, env: Environment, docnames: list[str]) -> None:
    logger.warning("Docnames: %r", docnames)


def setup(app: Sphinx) -> None:
    """Install the extension into the Sphinx ``app``."""

    app.add_config_value("sphinx_gooey_conf", {}, "html")
    app.add_directive("example-gallery", ExampleGallery)

    # If myst_nb is set up after myst_parser there are conflicts about common
    # configuration options and directives. So we can't set up myst_nb only when
    # the Jupyter stuff is loaded, it has to come here.
    try:
        app.setup_extension("myst_nb")
    except ExtensionError:
        app.setup_extension("myst_parser")
    app.setup_extension("sphinx_design")

    # Ignoring the example files has to be done when config is initialized, doing this
    # when the builder is initialized is already too late and we get the warning
    app.connect("config-inited", ignore_example_files)
    # The priority of loading the generators has to be lower than generating the
    # Markdown so that loading is run first.
    # These are done when the builder is initialized so that the environment is created
    # and we can store the generators on the environment.
    app.connect("builder-inited", load_generator_entry_points, priority=501)
    # app.connect("builder-inited", generate_example_md, priority=502)
    app.connect("env-get-outdated", add_fake_files)
    app.connect("env-before-read-docs", env_before_read_docs)
    logger.info("Set up sphinx_gooey!")
