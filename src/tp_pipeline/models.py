"""
models.py
-------------
Defines the domain model: Transaction (a single cleaned journal posting),
Entity (a legal entity with its P&L and derived TP classification), and
TPDataset (the container that holds every Transaction and Entity the
pipeline works with).
"""

class Transaction:

    def __init__(self, transaction_id, posting_date, booking_text, company_code, partner_company_code, gl_account, transaction_group, transaction_type, amount, currency, is_intercompany):

        self.transaction_id = transaction_id
        self.posting_date = posting_date
        self.booking_text = booking_text
        self.company_code = company_code
        self.partner_company_code = partner_company_code
        self.gl_account = gl_account
        self.transaction_group = transaction_group
        self.transaction_type = transaction_type
        self.amount = amount
        self.currency = currency
        self.is_intercompany = is_intercompany

class Entity:

    def __init__(self, company_code, entity_name, country_name, region, currency):

        self.company_code = company_code
        self.entity_name = entity_name
        self.country_name = country_name
        self.region = region
        self.currency = currency

        self.period = None
        self.revenue = 0.0
        self.cogs = 0.0
        self.sga = 0.0
        self.rd = 0.0
        self.other_opex = 0.0
        self.functional_role = {}

    def load_financials(self, row):
        self.period = row["Period"]
        self.revenue = row["Revenue"]
        self.cogs = row["COGS"]
        self.sga = row["SGA"]
        self.rd = row["RD"]
        self.other_opex = row["OtherOpex"]

    @property
    def operating_profit(self):
        return self.revenue - self.cogs - self.sga - self.rd - self.other_opex

    @property
    def operating_margin_pct(self):
        if self.revenue == 0:
            return 0
        else:
            return round(self.operating_profit / self.revenue * 100,2)

    @property
    def full_cost_markup_pct(self):
        total_costs=self.cogs + self.sga + self.rd + self.other_opex

        if total_costs==0:
            return 0
        else:
            return round((self.revenue-total_costs) / total_costs * 100, 2)

    @property
    def revenue_lc(self):
        return self.revenue

    @property
    def operating_profit_lc(self):
        return self.operating_profit

    def revenue_eur(self, fx_rate_lookup):
        return round(self.revenue * fx_rate_lookup[self.currency], 2)

    def operating_profit_eur(self, fx_rate_lookup):
        return round(self.operating_profit * fx_rate_lookup[self.currency], 2)

    def cogs_eur(self, fx_rate_lookup):
        return round(self.cogs * fx_rate_lookup[self.currency], 2)

    def sga_eur(self, fx_rate_lookup):
        return round(self.sga * fx_rate_lookup[self.currency], 2)

    def rd_eur(self, fx_rate_lookup):
        return round(self.rd * fx_rate_lookup[self.currency], 2)

    def other_opex_eur(self, fx_rate_lookup):
        return round(self.other_opex * fx_rate_lookup[self.currency], 2)

class TPDataset:

    def __init__(self):
        self.transactions = []
        self.entities = {}

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def register_entity(self, entity):
        self.entities[entity.company_code]=entity

    def grand_total_journal(self):
        return round(sum(t.amount for t in self.transactions), 2)

    def grand_total_revenue(self):
        return round(sum(e.revenue for e in self.entities.values()), 2)

if __name__ == "__main__":
    tx = Transaction(
        transaction_id="TX00001", posting_date="2025-04-11",
        booking_text="Sale of finished pharmaceuticals to distributor DE01",
        company_code="US02", partner_company_code="DE01", gl_account="4000",
        transaction_group="Distribution", transaction_type="Invoice",
        amount=55471.96, currency="USD", is_intercompany=True
    )
    print(tx.__dict__)

    de01 = Entity(company_code="DE01", entity_name="PharmaCorp Deutschland GmbH", country_name="Germany", region="EMEA", currency="EUR")
    de01.load_financials({"Revenue": 445521.63, "COGS": 380087.42, "SGA": 40365.04, "RD": 0.0, "OtherOpex": 9490.96, "Period": "FY2025"})

    print(de01.__dict__)
    print(de01.operating_margin_pct)
    print(de01.revenue_lc)
    print(de01.operating_profit_lc)

    fx_rate_lookup = {"EUR": 1.0, "USD": 0.92, "CHF": 1.04, "SGD": 0.68}
    print(de01.revenue_eur(fx_rate_lookup))
    print(de01.operating_profit_eur(fx_rate_lookup))

    dataset = TPDataset()
    dataset.add_transaction(tx)
    dataset.register_entity(de01)

    print(dataset.grand_total_journal())
    print(dataset.grand_total_revenue())