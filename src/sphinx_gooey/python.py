import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from textwrap import dedent
from typing import TypedDict

from sphinx.util.logging import getLogger

logger = getLogger(__name__)


@dataclass
class Example:
    source_path: Path
    source_folder: Path
    target_path: Path
    name: str = ""
    reference: str = ""
    summary: str = ""
    category: str = ""

    def __post_init__(self) -> None:
        self.name = self.source_path.name
        has_subdir = (
            len(self.source_path.relative_to(self.source_folder.parent).parts) > 2
        )
        if has_subdir:
            self.reference = f"{self.source_path.parts[-2]}-{self.source_path.stem}"
            self.category = self.source_path.parts[-2]
        else:
            self.reference = self.source_path.stem

        self.reference = self.reference.replace("_", "-").replace(" ", "")


@dataclass
class PythonExample(Example):
    def __post_init__(self) -> None:
        super().__post_init__()

        mod = ast.parse(self.source_path.read_bytes())
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


class Config(TypedDict):
    categories: dict[str, str]


def md_generator(source_folder: Path, target_folder: Path, config: Config) -> None:
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
                    reference=example.reference,
                )
                for example in these_examples
            ]
        )
        block_text.extend(category_block.format(content=block_content).splitlines())

    source_index = source_folder / "index.md"
    target_index = target_folder / "index.md"
    if source_index.is_file():
        copy2(source_index, target_index)
    else:
        target_index.touch()
    with target_index.open("a") as fp:
        fp.write("\n")
        fp.write("\n".join(block_text))


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
        example_file = ff.relative_to(source_folder)
        target_file = (target_folder / example_file).with_suffix(".md")
        target_file.parent.mkdir(exist_ok=True, parents=True)
        example = PythonExample(ff, source_folder, target_file)
        examples[example.category].append(example)
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
