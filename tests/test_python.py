from pathlib import Path

from sphinx_gooey.python import PythonExample


def test_python_example(tmp_path: Path) -> None:
    py_file_text = """'''Summary line'''\nimport os\nprint(os.cwd())"""
    py_file = tmp_path / "test.py"
    py_file.write_text(py_file_text)
    py_ex = PythonExample(py_file, tmp_path)
    assert py_ex.summary == "Summary line."
    assert py_ex.reference == "test"
    assert py_ex.category == ""


def test_python_example_with_subdir(tmp_path: Path) -> None:
    py_file_text = """'''Summary line'''\nimport os\nprint(os.cwd())"""
    subdir = tmp_path / "subdir"
    subdir.mkdir(exist_ok=True, parents=True)
    py_file = subdir / "test.py"
    py_file.write_text(py_file_text)
    py_ex = PythonExample(py_file, tmp_path)
    assert py_ex.summary == "Summary line."
    assert py_ex.reference == f"{subdir.stem}-{py_file.stem}"
    assert py_ex.category == subdir.stem
