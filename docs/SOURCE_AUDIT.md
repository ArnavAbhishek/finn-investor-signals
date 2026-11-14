# Source audit and numerical provenance

## Featured company: Infosys Limited (INFY)

Historical, frozen official-source case with evidence dated through **23 October 2026**. All information in this section comes from **the issuer**; it is not a Yahoo quote, a third-party broker note or a model-generated fact.

### Direct official issuer references

- FY2025–26 **Integrated Annual Report**: https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-26.pdf
- Infosys **financial data sheet**: https://www.infosys.com/investors/reports-filings/financials/data-sheet.html
- Q3 FY26 corporate fact sheet: https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q3/documents/fact-sheet.pdf
- Q4 FY26 corporate fact sheet: https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q4/documents/fact-sheet.pdf
- Q1 FY27 corporate fact sheet: https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q1/documents/fact-sheet.pdf
- Q2 FY27 corporate fact sheet: https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2/documents/fact-sheet.pdf
- Q2 FY27 earnings-call transcript, 23 October 2026: https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2/documents/transcripts/earningscall.pdf
- Q2 FY27 investor results hub: https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2.html

### Recorded quarterly financial data

The app uses **consolidated IFRS, INR crore**. `app/services/casebook.py` carries a page pointer for each quarter.

| Period | Revenue | Operating profit | PBT | PAT | Operating margin | Evidence |
|---|---:|---:|---:|---:|---:|---|
| Q3 FY26 | 45,479 | 8,355 | 9,229 | 6,654 | 18.4% | Q4 FY26 fact sheet, p. 5 |
| Q4 FY26 | 46,402 | 9,743 | 10,797 | 8,501 | 21.0% | Q4 FY26 fact sheet, p. 5 |
| Q1 FY27 | 48,211 | 10,163 | 11,028 | 7,769 | 21.1% | Q1 FY27 fact sheet, p. 3 |
| Q2 FY27 | 49,244 | 10,330 | 11,063 | 7,823 | 21.0% | Q2 FY27 fact sheet, p. 4 |

Year-ago comparator for Q2 FY27: Q2 FY26 Revenue ₹44,490 crore, PBT ₹10,229 crore, PAT ₹7,364 crore (Q2 FY27 company fact sheet). The app computes QoQ/YoY from these actual source figures.

**EBITDA intentionally omitted**: a company-reported “operating profit” value is not automatically EBITDA. If the primary source does not state or support that figure with a reliable reconciliation, the app displays **Not verified**. This is an intentional financial integrity choice, not a UI bug.

### Narrative vs numbers

Company Q2 FY27 management call indicated cautious discretionary spending and revised FY27 constant-currency revenue growth guidance to **1%–2%**, maintaining **20%–22% operating margin** guidance. That is **forward full-year guidance**; it must not be scored as delivered/missed using quarterly INR reported growth. FINN surfaces that mismatch explicitly rather than creating a fake “management reliability” score.

Other shown facts: FY26 FCF ₹33,097 crore and 112.3% FCF conversion, as represented in annual report; business mix, ROE and balance-sheet figures are cited to company reports. Always open the original PDF for your submission demo.

### Provenance model

- `source_url` points to the issuer PDF/webpage.
- `page` is 1-based for PDF links (`#page=4`, etc.). PDF page references are *document viewer pages*, not necessarily printed page numbers.
- `kind: verified_historical_case`, `as_of`, and `not_live: true` distinguish historical evidence from current market data.
- For **other companies** the engine only retrieves snippets from indexed PDFs, labelling them as **verbatim source excerpts**, not audited financial conclusions.
- NSE filings should carry the exchange filing URL and filing date, and be verified before sharing.

### Accounting comparison formula

\[ \text{QoQ\%} = \frac{\text{current quarter} - \text{previous quarter}}{|\text{previous quarter}|} \times 100 \]

\[ \text{YoY\%} = \frac{\text{current quarter} - \text{same quarter last year}}{|\text{same quarter last year}|} \times 100 \]

No growth percentage is calculated with a zero or absent base. INR reporting basis, standalone/consolidated scope, restatements and segment changes must be checked before cross-period interpretation.

## Disclosure

Do not confuse source-linked **historical fundamentals** with real-time price/volume feeds. An unavailable public quote cannot be replaced with one of these figures, nor vice versa.
