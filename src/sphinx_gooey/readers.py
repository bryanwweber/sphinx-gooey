import nbformat as nbf


def example_reader(source: str) -> nbf.NotebookNode:
    return nbf.read(source.removesuffix(".md"), nbf.current_nbformat)
