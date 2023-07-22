from importlib.metadata import entry_points, version
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config as SphinxConfig
from sphinx.errors import ExtensionError
from sphinx.util.logging import getLogger

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

    generators = app.config.sphinx_gooey_conf.get("generators")
    if generators is None:
        raise ValueError("No generators available")

    srcdir = Path(app.builder.srcdir)
    for name, values in app.config.sphinx_gooey_conf["sources"].items():
        source_folder = (srcdir / values["source"]).resolve()
        logger.info("Working with %s", source_folder)
        if not source_folder.is_dir():
            raise ValueError(
                f"Source folder for examples must exist: '{source_folder!s}'"
            )
        target_folder = (srcdir / values["target"]).resolve()
        generator = generators[name].load()
        generator(source_folder, target_folder, values)

        # references = set(e.reference for e in examples)
        # if len(references) != len(examples):
        #     logger.error(
        #         "There are duplicate path names in the set of examples: %r", examples
        #     )
        #     sys.exit(1)

        # app.config.sphinx_gooey_conf[name]["examples"] = examples


def load_generator_entry_points(app: Sphinx, config: SphinxConfig) -> None:
    config.sphinx_gooey_conf["generators"] = entry_points(
        group="sphinx_gooey.generators"
    )


def setup(app: Sphinx) -> dict[str, bool | str]:
    """Install the extension into the Sphinx ``app``."""
    # If myst_nb is set up after myst_parser there are conflicts about common
    # configuration options and directives. So we can't set up myst_nb only when
    # the Jupyter stuff is loaded, it has to come here.
    try:
        app.setup_extension("myst_nb")
    except ExtensionError:
        app.setup_extension("myst_parser")
    app.setup_extension("sphinx_design")

    app.add_config_value("sphinx_gooey_conf", {}, "html")
    app.connect("config-inited", load_generator_entry_points, priority=10)
    app.connect("builder-inited", generate_example_md, priority=10)

    # sphinx-gallery creates the reST files for examples and the index using a
    # builder-inited event

    # The priority of loading the generators has to be lower than generating the
    # Markdown so that loading is run first.
    logger.info("Set up sphinx_gooey!")
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": version("sphinx-gooey"),
    }
