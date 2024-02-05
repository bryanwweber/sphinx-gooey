from pathlib import Path

from sphinx_gooey.python import PythonExample, file_generator


def test_python_example(tmp_path: Path) -> None:
    py_file_text = """'''Summary line'''\nimport os\nprint(os.cwd())"""
    py_file = tmp_path / "test.py"
    py_file.write_text(py_file_text)
    py_ex = PythonExample(py_file, tmp_path, target_path=Path.cwd())
    assert py_ex.summary == "Summary line."
    assert py_ex.reference == "test"
    assert py_ex.category == ""


def test_python_example_with_subdir(tmp_path: Path) -> None:
    py_file_text = """'''Summary line'''\nimport os\nprint(os.cwd())"""
    subdir = tmp_path / "subdir"
    subdir.mkdir(exist_ok=True, parents=True)
    py_file = subdir / "test.py"
    py_file.write_text(py_file_text)
    py_ex = PythonExample(py_file, tmp_path, target_path=Path.cwd())
    assert py_ex.summary == "Summary line."
    assert py_ex.reference == f"{subdir.stem}-{py_file.stem}"
    assert py_ex.category == subdir.stem


def test_file_generator(tmp_path: Path) -> None:
    py_file_text = """'''Summary line'''\nimport os\nprint(os.cwd())"""
    rootdir = tmp_path / "python"
    rootdir.mkdir(exist_ok=True, parents=True)
    py_file_root = rootdir / "test1.py"
    py_file_root.write_text(py_file_text)
    subdir = rootdir / "subdir"
    subdir.mkdir(exist_ok=True, parents=True)
    py_file_sub = subdir / "test.py"
    py_file_sub.write_text(py_file_text)
    target_path = tmp_path / "target"
    examples = file_generator(tmp_path, target_path)
    assert len(examples) == 2
    for example in examples.values():
        for ex in example:
            assert py_file_text in ex.target_path.read_text()
