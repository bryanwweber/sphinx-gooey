from pathlib import Path

from sphinx_gooey.python import PythonExample


def test_python_example_has_summary(tmp_path: Path) -> None:
    py_file_text = """'''Summary line'''\nimport os\nprint(os.cwd())"""
    py_file = tmp_path / "test.py"
    py_file.write_text(py_file_text)
    py_ex = PythonExample(py_file, tmp_path)
    assert py_ex.summary
