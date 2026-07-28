# Python Concepts → Where They Live

This project is structured like a real project first (grouped by
responsibility), not by "which Python feature does this file teach". This
page is the map for the second view: if you want to see a specific Python
fundamental in action, here's exactly where to look.

| Python concept | File | What to look at |
|---|---|---|
| **Numbers** | `src/tp_pipeline/benchmarking.py` | `calculate_operating_margin_pct()`, `calculate_full_cost_markup_pct()`, `calculate_royalty_rate_pct()` |
| **Indexing & Slicing with Strings** | `src/tp_pipeline/cleaning.py` | `split_company_code()` (`code[:2]`, `code[2:]`), `extract_entity_code_from_booking_text()` |
| **Lists vs. Tuples (mutable/immutable)** | `src/tp_pipeline/lookups.py` | `IN_SCOPE_ENTITIES` (list), `STATIC_BENCHMARK_RANGES` (tuple), `demonstrate_tuple_immutability()` |
| **Dictionaries** | `src/tp_pipeline/lookups.py` | `build_gl_account_mapping()`, `build_benchmark_lookup()`, `build_entity_master_lookup()`, `build_fx_rate_lookup()` |
| **I/O Basics** | `src/tp_pipeline/data_io.py` | `read_erp_export()`, `read_entity_financials()`, `read_mapping_file()`, `read_benchmark_file()`, `read_entity_master()`, `read_fx_rates()` |
| **Booleans** | `src/tp_pipeline/reconciliation.py` | `flag_intercompany()` (IC/3P mask), `reconciles()` (tolerance-based total check) |
| **Comparison Operators** | `src/tp_pipeline/benchmarking.py` | `classify_against_benchmark()` - chained comparisons against Min/LowerQuartile/UpperQuartile/Max |
| **For and While Loops** | `src/tp_pipeline/cleaning.py` | `enrich_rows_with_for_loop()` (for), `simulate_paged_extraction()` (while) |
| **Functions** | `src/tp_pipeline/cleaning.py` | `clean_transaction_row()`, `clean_financials_row()`, `summarize_amounts()` (*args), `build_transaction()` (**kwargs) |
| **The map() Function** | `src/tp_pipeline/cleaning.py` | `clean_all_transactions_with_map()`, `clean_all_financials_with_map()` |
| **LEGB Rule** | `src/tp_pipeline/currency.py` | `make_fx_converter()` - a closure over `fx_rate` (Enclosing scope), `REPORTING_CURRENCY` (Global scope) |
| **Object Oriented Programming** | `src/tp_pipeline/models.py` | `Transaction`, `Entity` (with `@property` methods), `TPDataset` |
| **Error Handling** | `src/tp_pipeline/exceptions.py` + `src/tp_pipeline/cleaning.py` | `MappingNotFoundError`, `FinancialsNotFoundError` (definitions); `get_transaction_group()`, `process_rows_safely()` (try/except/else/finally in use) |
| **Generators (yield)** | `src/tp_pipeline/data_io.py` | `stream_clean_transactions()` |
| **`collections` module** | `src/tp_pipeline/roles.py` | `Counter` in `most_invoiced_gl_account()`, `derive_functional_role()`, `transaction_group_counts()` |
| **Python Debugger (pdb)** | `src/tp_pipeline/debug_utils.py` | `suspicious_margin_calculation()` - flip `DEBUG_MODE = True` and run it directly |

## Why this structure instead of "one file per concept"

An earlier version of this project had one file per Python topic
(`c01_numbers.py`, `c02_strings.py`, ...). That's a fine structure for a
tutorial, but it's not how real software gets organized - a reviewer
looking at a repo structured that way will read it as a course exercise,
not as evidence of production-code judgment.

Real projects group code by **what it's responsible for** (reading data,
cleaning data, calculating a metric, the domain model, ...). Every Python
fundamental from the original list is still here and still exercised -
this file exists so you don't lose that mapping just because the folder
structure changed.
