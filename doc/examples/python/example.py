"""
This file is an example of a Python file for the example gallery. It uses lots of
things and this is the summary.

Some more text comes after the summary to make sure it makes sense.
"""
from pathlib import Path

HERE = Path(__file__).parent

for ff in HERE.iterdir():
    print(ff.name)
