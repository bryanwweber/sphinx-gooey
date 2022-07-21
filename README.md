# Sphinx-Gooey

The Sphinx Gallery Of Outstanding Examples extension.

Produce a gallery of HTML examples from code in any language for a
Sphinx-generated website. The code examples are highlighted by the built-in
features of Sphinx and the gallery index page is created with the [`sphinx-design`](https://sphinx-design.readthedocs.io/)
extension using modern grids and cards with the Bootstrap framework.

**Warning:** This extension is undergoing heavy, active development. Some
things will not work, things will break unexpectedly, and there are dragons
afoot. Please don't use this extension for production (yet!).

Inspired by [`sphinx-gallery`](https://sphinx-gallery.github.io/),
`sphinx-gooey` offers some unique features that make it particularly useful for
projects that maintain examples in a number of programming languages.

| Feature | `sphinx-gooey` | `sphinx-gallery` |
|-|-|-|
| Highlight Python code in HTML | ✅ | ✅ |
| Execute Python code to insert results inline | | ✅ |
| Highlight Jupyter Notebooks in HTML | ✅ | * |
| Execute Jupyter Notebooks to insert results inline | ✅ | |
| Highlight C/C++/Fortran/Rust/... code in HTML | ✅ | |
| Use [MyST markup](https://myst-parser.readthedocs.io/) in Jupyter Notebooks | ✅ | |
| Link to other documentation in example files | | ✅ |
| Download the source code for a rendered example | ✅ | ✅ |

\* `sphinx-gallery` allows you to write `rST` text as comments in your script,
a format that can be created from a Notebook file using `nbconvert`.

## Installation

Don't do it. If you must, `pip install -e .` from the source folder should
work. You might need to install [`pdm`](https://pdm.fming.dev/2.0/).

## Usage

Don't do it. See the `doc` folder if you must.
