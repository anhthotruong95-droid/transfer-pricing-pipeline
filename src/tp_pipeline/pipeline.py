"""
pipeline.py
---------------
The orchestrator. This is the only module that imports from ALL the other
modules and calls them in order - every individual module stays focused on
its own responsibility (I/O, cleaning, roles, benchmarking, reconciliation,
currency, the domain model), and this file wires them together into one
runnable pipeline. `main.py` at the project root just calls run_pipeline().
"""
