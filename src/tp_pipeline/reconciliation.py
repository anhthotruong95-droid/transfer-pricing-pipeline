"""
reconciliation.py
---------------------
Checks whether two totals (e.g. journal vs. financials) tie out within a
small tolerance.
"""


def reconciles(original_total, comparison_total, tolerance=1.0):
    return abs(original_total - comparison_total) <= tolerance


if __name__ == "__main__":
    print("Reconciles (should be True):", reconciles(1000.0, 1000.5))
    print("Reconciles (should be False):", reconciles(1000.0, 1050.0))