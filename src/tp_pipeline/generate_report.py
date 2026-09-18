"""
generate_report.py
----------------------
Generates a management summary of the Transfer Pricing benchmark
results, as charts and a PDF report.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
FINANCIALS_FILE = OUTPUT_DIR / "financial_statements.csv"
IC_VOLUME_FILE = OUTPUT_DIR / "intercompany_transaction_volume.csv"
MARGIN_CHART_FILE = OUTPUT_DIR / "distributor_margin_chart.png"
MARKUP_CHART_FILE = OUTPUT_DIR / "manufacturer_markup_chart.png"
IC_PIE_REPORTING_FILE = OUTPUT_DIR / "ic_volume_pie_reporting.png"
IC_PIE_PARTNER_FILE = OUTPUT_DIR / "ic_volume_pie_partner.png"
REPORT_FILE = OUTPUT_DIR / "benchmark_report.pdf"


def _draw_benchmark_chart(entities, value_col, title, chart_file):
    """Shared chart logic: bar per entity, colored by BenchmarkStatus,
    with that entity's own region-specific benchmark quartile range
    drawn as a dashed span above/below the bar."""
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4.2))

    colors_ = ["#c96a6a" if status == "Out of Range" else "#6ba368"
               for status in entities["BenchmarkStatus"]]
    bars = ax.bar(entities["CompanyCode"], entities[value_col], color=colors_, width=0.5)

    # Keep bar width and spacing visually consistent whether there's 1
    # entity or 4 - without this, a single bar would stretch to fill the
    # whole axis. Centers the actual bars within a fixed-width "slot" area.
    n = len(entities)
    slots = max(n, 4)
    pad = (slots - n) / 2
    ax.set_xlim(-0.75 - pad, n - 0.25 + pad)

    for i, (_, row) in enumerate(entities.iterrows()):
        ax.plot([i - 0.25, i + 0.25], [row["BenchmarkLowerQuartile"]] * 2,
                color="black", linestyle="--", linewidth=1)
        ax.plot([i - 0.25, i + 0.25], [row["BenchmarkUpperQuartile"]] * 2,
                color="black", linestyle="--", linewidth=1)

    for bar, value in zip(bars, entities[value_col]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.15, f"{value:.1f}%",
                ha="center", fontsize=9)

    ax.set_title(title, fontsize=12)
    ax.set_ylabel(value_col.replace("Pct", " (%)"))
    ax.set_xlabel("Entity")

    legend_elements = [
        Patch(facecolor="#6ba368", label="Within Range"),
        Patch(facecolor="#c96a6a", label="Out of Range"),
        Line2D([0], [0], color="black", linestyle="--", label="Benchmark quartile"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8)

    plt.tight_layout()
    plt.savefig(chart_file, dpi=150)
    plt.close(fig)


def create_margin_chart(distributors):
    _draw_benchmark_chart(
        distributors, "OperatingMarginPct",
        "Distributor Operating Margin vs. Region Benchmark Range",
        MARGIN_CHART_FILE,
    )


def create_markup_chart(manufacturers):
    _draw_benchmark_chart(
        manufacturers, "FullCostMarkupPct",
        "Contract Manufacturer Full Cost Mark-up vs. Region Benchmark Range",
        MARKUP_CHART_FILE,
    )


def _draw_ic_pie_chart(series, title, chart_file):
    """Shared pie chart logic for IC volume breakdowns. Wedge labels show
    both the EUR amount and the percentage share."""
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(6, 6))
    palette = sns.color_palette("pastel", n_colors=len(series))

    total = series.sum()

    def amount_and_pct(pct):
        amount = pct / 100 * total
        return f"{amount:,.0f} EUR\n({pct:.1f}%)"

    ax.pie(
        series.values,
        labels=series.index,
        autopct=amount_and_pct,
        colors=palette,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1},
        textprops={"fontsize": 11},
    )
    ax.set_title(title, fontsize=17)
    ax.axis("equal")

    plt.tight_layout()
    plt.savefig(chart_file, dpi=150)
    plt.close(fig)


def create_ic_volume_pie_charts(ic_volume_df):
    """Two pie charts: IC volume by ReportingEntity (who invoices) and
    by TransactionPartner (who receives) - kept separate rather than
    combined, since summing both sides per entity would double-count
    each transaction and blur who is actually invoicing whom."""
    by_reporting = ic_volume_df.groupby("ReportingEntity")["TotalAmountEUR"].sum().sort_values(ascending=False)
    by_partner = ic_volume_df.groupby("TransactionPartner")["TotalAmountEUR"].sum().sort_values(ascending=False)

    _draw_ic_pie_chart(by_reporting, "Intercompany Volume by Reporting Entity (EUR)", IC_PIE_REPORTING_FILE)
    _draw_ic_pie_chart(by_partner, "Intercompany Volume by Transaction Partner (EUR)", IC_PIE_PARTNER_FILE)

    return by_reporting, by_partner


_NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                  6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def _as_word(n):
    return _NUMBER_WORDS.get(n, str(n))


def _join_and(items):
    """Joins a list into 'A', 'A and B', or 'A, B, and C'."""
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def build_summary_text(benchmarked_df, by_reporting=None, by_partner=None):
    total = len(benchmarked_df)
    out_of_range = benchmarked_df[benchmarked_df["BenchmarkStatus"] == "Out of Range"]
    n_out = len(out_of_range)

    if n_out == 0:
        benchmark_sentence = (f"Of the {_as_word(total)} benchmarked entities, all fall within their "
                               f"respective arm's-length ranges.")
    else:
        only = "only " if n_out == 1 else ""
        if n_out == 1:
            row = next(out_of_range.itertuples())
            detail = f"{row.CompanyCode} falls outside its regional arm's-length range, with a margin of {row.OperatingMarginPct:.2f}%,"
        else:
            names = _join_and([row.CompanyCode for row in out_of_range.itertuples()])
            detail = f"{names} fall outside their regional arm's-length ranges"
        benchmark_sentence = (
            f"Of the {_as_word(total)} benchmarked entities, {only}{detail} while the remaining "
            f"entities fall within their respective arm's-length ranges."
        )

    if by_reporting is None or by_reporting.empty:
        return benchmark_sentence

    reporting_names = _join_and(by_reporting.index.tolist())
    partner_names = _join_and(by_partner.head(3).index.tolist())
    volume_sentence = (
        f"{reporting_names} report the highest IC volumes on the invoicing side, while "
        f"{partner_names} account for the highest IC volumes on the receiving side."
    )

    return f"{volume_sentence} {benchmark_sentence}"


def build_results_table(benchmarked_df):
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=8, leading=10, alignment=TA_CENTER)
    header_style = ParagraphStyle("cell_header", parent=cell_style, textColor=colors.white)

    header = ["Entity", "Region", "Role", "PLI Indicator", "PLI Value", "Benchmark Range", "Study Source", "Status"]
    rows = [[Paragraph(h, header_style) for h in header]]
    row_colors = []  # background color per data row, aligned with BenchmarkStatus

    for row in benchmarked_df.itertuples():
        if row.FunctionalRole == "Distributor":
            pli_indicator = "OM %"
            pli_value = f"{row.OperatingMarginPct:.2f}%"
        else:
            pli_indicator = "FCM %"
            pli_value = f"{row.FullCostMarkupPct:.2f}%"
        bench_range = f"{row.BenchmarkLowerQuartile:.1f}% - {row.BenchmarkUpperQuartile:.1f}%"
        rows.append([
            Paragraph(row.CompanyCode, cell_style),
            Paragraph(row.Region, cell_style),
            Paragraph(row.FunctionalRole, cell_style),
            Paragraph(pli_indicator, cell_style),
            Paragraph(pli_value, cell_style),
            Paragraph(bench_range, cell_style),
            Paragraph(row.BenchmarkStudySource, cell_style),
            Paragraph(row.BenchmarkStatus, cell_style),
        ])
        row_colors.append(
            colors.HexColor("#f8d7da") if row.BenchmarkStatus == "Out of Range" else colors.HexColor("#d4edda")
        )

    table = Table(rows, colWidths=[1.4 * cm, 1.4 * cm, 2.2 * cm, 1.6 * cm, 1.6 * cm, 2.2 * cm, 4 * cm, 1.8 * cm])
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    # Only color the Status column (last column, index -1) - row index
    # i+1 because row 0 is the header.
    for i, color in enumerate(row_colors):
        table_style.append(("BACKGROUND", (-1, i + 1), (-1, i + 1), color))
    table.setStyle(TableStyle(table_style))
    return table


def build_report_pdf(summary_text, table, has_distributors, has_manufacturers, period, has_ic_volume):
    styles = getSampleStyleSheet()
    summary_style = ParagraphStyle("summary", parent=styles["BodyText"], alignment=TA_JUSTIFY)
    doc = SimpleDocTemplate(str(REPORT_FILE), pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm)

    story = [
        Paragraph(f"Transfer Pricing Benchmark Report {period.replace('FY', '')}", styles["Title"]),
        Spacer(1, 0.3 * cm),
        Paragraph("Summary", styles["Heading2"]),
        Spacer(1, 0.2 * cm),
        Paragraph(summary_text, summary_style),
        Spacer(1, 0.5 * cm),
    ]

    if has_distributors or has_manufacturers:
        story += [
            Paragraph("Benchmark results by entity", styles["Heading2"]),
            Spacer(1, 0.2 * cm),
        ]
    if has_distributors:
        story += [Image(str(MARGIN_CHART_FILE), width=16 * cm, height=8.4 * cm), Spacer(1, 0.4 * cm)]
    if has_manufacturers:
        story += [Image(str(MARKUP_CHART_FILE), width=16 * cm, height=8.4 * cm), Spacer(1, 0.4 * cm)]

    story += [
        Paragraph("Detailed benchmark results by entity", styles["Heading2"]),
        Spacer(1, 0.2 * cm),
        table,
    ]

    if has_ic_volume:
        story += [
            Spacer(1, 0.6 * cm),
            Paragraph("Intercompany transaction volume", styles["Heading2"]),
            Spacer(1, 0.2 * cm),
            Image(str(IC_PIE_REPORTING_FILE), width=12 * cm, height=12 * cm),
            Spacer(1, 0.3 * cm),
            Image(str(IC_PIE_PARTNER_FILE), width=12 * cm, height=12 * cm),
        ]

    doc.build(story)


def main():
    df = pd.read_csv(FINANCIALS_FILE)

    # The Principal is never benchmarked - only Distributors and the
    # Contract Manufacturer have a meaningful BenchmarkStatus.
    benchmarked_df = df[df["BenchmarkStatus"].notna()].copy()
    distributors = benchmarked_df[benchmarked_df["FunctionalRole"] == "Distributor"].sort_values("OperatingMarginPct")
    manufacturers = benchmarked_df[benchmarked_df["FunctionalRole"] == "Contract Manufacturer"].sort_values("FullCostMarkupPct")

    if not distributors.empty:
        create_margin_chart(distributors)
    if not manufacturers.empty:
        create_markup_chart(manufacturers)

    has_ic_volume = IC_VOLUME_FILE.exists()
    by_reporting = by_partner = None
    if has_ic_volume:
        ic_volume_df = pd.read_csv(IC_VOLUME_FILE)
        by_reporting, by_partner = create_ic_volume_pie_charts(ic_volume_df)

    summary_text = build_summary_text(benchmarked_df, by_reporting, by_partner)
    table = build_results_table(benchmarked_df)
    period = benchmarked_df["Period"].iloc[0]
    build_report_pdf(summary_text, table, not distributors.empty, not manufacturers.empty, period, has_ic_volume)

    if not distributors.empty:
        print(f"Distributor chart saved to: {MARGIN_CHART_FILE}")
    if not manufacturers.empty:
        print(f"Manufacturer chart saved to: {MARKUP_CHART_FILE}")
    if has_ic_volume:
        print(f"IC volume pie charts saved to: {IC_PIE_REPORTING_FILE}, {IC_PIE_PARTNER_FILE}")
    print(f"Report saved to: {REPORT_FILE}")
    print(summary_text)


if __name__ == "__main__":
    main()