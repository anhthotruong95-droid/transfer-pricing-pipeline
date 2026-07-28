"""
debug_utils.py
------------------
Python concept covered: the Python Debugger (pdb) - instead of sprinkling
print() everywhere, drop a breakpoint into the code and inspect variables
live, step line-by-line, etc.

This lives in its own small module because it's a development/debugging
tool, not a piece of pipeline logic - you wouldn't import this from
pipeline.py in a real project, you'd reach for it manually while
investigating a specific bug.

How to actually use this file
------------------------------
Run it directly from a terminal (breakpoints don't do much inside a
notebook-style tool call):

    python3 -m tp_pipeline.debug_utils        # from src/
    (or) python3 src/tp_pipeline/debug_utils.py

Useful pdb commands once you hit the breakpoint:
    n        -> next line
    s        -> step into a function call
    p <expr> -> print an expression, e.g. p revenue
    c        -> continue running
    q        -> quit the debugger
"""


