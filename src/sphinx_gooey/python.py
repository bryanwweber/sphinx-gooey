import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from textwrap import dedent

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


ONE_CARD = dedent(
    """\
    :::{{grid-item-card}} {name}
    :link: {reference}
    :link-type: ref

    {summary}
    :::
    """
)


def md_generator(source_folder: Path, target_folder: Path) -> None:
    examples = file_generator(source_folder, target_folder)

    category_block = "::::{{grid}} 3\n{content}\n::::"
    block_text = []
    for category, these_examples in examples.items():
        block_text.append(f"## {category}")
        block_content = "\n".join(
            [
                ONE_CARD.format(
                    name=example.name,
                    summary=example.summary,
                    reference=example.reference,
                )
                for example in these_examples
            ]
        )
        block_text.extend(category_block.format(content=block_content).splitlines())

    copy2(source_folder.joinpath("index.md"), target_folder.joinpath("index.md"))
    with target_folder.joinpath("index.md").open("a") as fp:
        fp.write("\n")
        fp.write("\n".join(block_text))

    # return examples


def file_generator(
    source_folder: Path, target_folder: Path
) -> dict[str, list[PythonExample]]:
    examples: dict[str, list[PythonExample]] = defaultdict(list)
    extension = "*.py"
    for ff in source_folder.rglob(extension):
        if " " in str(ff):
            logger.warning(
                "The example '%s' has a space in the pathname which is not yet "
                "supported.",
                ff,
            )
            continue
        example = PythonExample(ff, source_folder)
        examples[example.category].append(example)
        example_file = ff.relative_to(source_folder)
        target_file = (target_folder / example_file).with_suffix(".md")
        copy2(ff, target_file.parent)

        target_file.write_text(
            f"""\
---
orphan: true
---
({example.reference})=
# {example.name}

[**Source**]({example_file.name})

```python
{ff.read_text()}
```
"""
        )
    return examples