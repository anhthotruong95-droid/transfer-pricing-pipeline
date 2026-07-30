"""
exceptions.py
----------------
Custom exception classes used across the pipeline. Kept in their own
module so multiple files (cleaning.py, pipeline.py) can raise and catch
the same, clearly named error types instead of each defining their own.
"""

class MappingNotFoundError(Exception):
    """Raised when a GL account has no entry in the mapping file"""
    pass