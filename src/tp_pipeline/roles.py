"""
roles.py
------------
Everything related to figuring out WHAT ROLE an entity plays, without
anyone having to maintain that as a manually-entered field.

Python concept covered: the `collections` module - Counter tells us which
GL account each entity invoices most often, and that tells us its role:
  - mostly GL 4100 (Contract Manufacturing fee)  -> Contract Manufacturer
  - mostly GL 4200 (Licensing/royalty)            -> Principal / IP Owner
  - mostly GL 4000, and it's an IC sale           -> Principal (selling to distributors)
  - mostly GL 4000, and it's a 3P sale            -> Distributor
"""

