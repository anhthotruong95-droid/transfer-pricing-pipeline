"""
main.py - Pharma Transfer Pricing Data Pipeline
=====================================================
Thin entry point. All the actual logic lives in src/tp_pipeline/ - see
README.md for the module map.

Run it with:
    python3 main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from tp_pipeline.pipeline import run_pipeline

if __name__ == "__main__":
    final_table, ic_volume_table = run_pipeline()
    print("\nFinal summary table:")
    print(final_table.to_string(index=False))
    print("\nIntercompany transaction volume:")
    print(ic_volume_table.to_string(index=False))