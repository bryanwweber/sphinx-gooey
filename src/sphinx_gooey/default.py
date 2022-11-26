import ast
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

from sphinx.application import Sphinx
from sphinx.util.logging import getLogger

logger = getLogger(__name__)


@dataclass
class Example:
    path: Path
    source_folder: Path
    name: str = ""
    reference: str = ""
    summary: str = ""
    category: str = ""

    def __post_init__(self) -> None:
        self.name = self.path.name
        has_subdir = len(self.path.relative_to(self.source_folder.parent).parts) > 2
        if has_subdir:
            self.reference = f"{self.path.parts[-2]}-{self.path.stem}"
            self.category = self.path.parts[-2]
        else:
            self.reference = self.path.stem

        self.reference = self.reference.replace("_", "-").replace(" ", "")


@dataclass
class PythonExample(Example):
    def __post_init__(self) -> None:
        super().__post_init__()

        mod = ast.parse(self.path.read_bytes())
        doc = ""
        for node in mod.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                doc = node.value.s.strip().split("\n\n")[0].strip()
                if not doc.endswith("."):
                    doc += "."
                break
        self.summary = doc


def md_generator(extension: str, app: Sphinx, source_folder: Path) -> list[Example]:
    examples: list[Example] = []
    for ff in source_folder.rglob(extension):
        pth = ff.relative_to(app.srcdir)
        if " " in str(pth):
            logger.warning(
                f"The example '{pth!s}' has a space in the "
                "pathname which is not yet supported."
            )
            continue
        if ff.suffix == ".py":
            example = PythonExample(ff, source_folder)
        else:
            example = Example(ff, source_folder)  # type: ignore
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
