"""
exceptions.py
-----------------
Custom exception classes for the pipeline.

Python concept covered: Error Handling (custom exceptions instead of
letting a generic KeyError/ValueError bubble up with no context).

These are intentionally kept in their own small module - real projects
define exceptions once, then raise/catch them from wherever they're
relevant (see cleaning.py and pipeline.py), instead of bundling
try/except logic and exception *definitions* into the same file.
"""