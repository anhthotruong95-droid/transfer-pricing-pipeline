"""
currency.py
---------------
Everything related to converting entity-local currency amounts into the
group reporting currency (EUR) using fx_rates.xlsx.

Python concept covered: LEGB scoping rule (Local, Enclosing, Global,
Built-in) - a closure that "remembers" a fixed FX rate per converter,
which is exactly what's needed here: one converter per currency.
"""


