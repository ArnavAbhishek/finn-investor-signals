# FINN — reviewer walkthrough, product decisions, and viva/interview preparation

## 1. Your 30-second explanation

> FINN is a mobile-first investor intelligence prototype built around **Push and Pull**. Push ranks exchange disclosures and unusual end-of-day price/volume moves so investors see the few developments that merit attention. Pull researches an issuer using its **own annual report, results and earnings-call transcripts**, exposes citations and compares actual outcomes with management's stated narrative. I used deterministic rules for measurable signals and financial arithmetic, and AI-assisted retrieval only where unstructured text adds value. The principal trade-off is that unofficial public NSE/Yahoo endpoints may not be reliably accessible on cloud infrastructure, so the prototype never invents market values when they are unavailable.

## 2. Product decisions you can defend

**Why not a general stock trading app?** ENAM wants an information filter, not trade placement. The overview's one large headline links to analysis; deeper information is behind deliberate actions. The app does not recommend buying or selling.

**Why the Infosys case?** A reproducible analysis based on actual issuer annual/quarterly documents and a management call proves that Pull can do more than paraphrase articles. It also works when an exchange or market-data provider is temporarily unavailable. It is **a historical research case**, not a replacement for live NSE prices.

**Why 18 stocks?** The brief requests a mock portfolio of 15–20 listed companies. The watchlist has 18 starting companies from multiple sectors, and lets the user customise the selection. It is not all of NSE; NSE has far more listed securities.

**Why four ad-hoc tickers?** The brief suggests 3–5 for on-demand research; HCLTECH, PIDILITIND, DIXON and DIVISLAB demonstrate ticker input outside the fixed watchlist. The engine retrieves only what their sourced PDF libraries support. No PDF means no invented answer.

**Why no fake live feed?** Financial misinformation is worse than a visible source error. Live mode requests public EOD and filing data. A clearly labelled, isolated fictional QA preview exists for testing, not as real evidence.

**Why not 60 widgets on home?** The user sees a strong entry point, the small watchlist snapshot and direct next actions. Dense source details are kept inside Research and Signals.

**Why auto refresh and manual recheck?** Automatic EOD fetching about every four minutes handles normal use. Manual **Recheck now** is specifically for overriding cached provider responses after an important filing or source recovery. It is globally rate-limited to avoid hammering free endpoints. Rechecking after market hours does not mean prices must change.

## 3. Exactly how the app works

### Push workflow

1. A user selects their followed NSE symbols; the browser stores watchlist and thresholds locally.
2. `/api/digest` requests public NSE corporate announcements for selected tickers and time window.
3. The server maps disclosure text into the **17 glossary announcement categories** and assigns a priority using deterministic signal rules.
4. The frontend sorts material events above routine filings, permits source opening, category/date filtering and investigation of the company.
5. `/api/prices` fetches verified historical end-of-day close and volume data using Yahoo Finance, with best-effort NSE fallback.
6. Rules compare a day's absolute price move with user-selected ±% and volume relative to recent average with user-selected multiple.
7. The browser rechecks about every four minutes while visible; it can notify the investor of newly arrived verified priority filings if browser permission was granted. It is **not** a server-side 24/7 notification daemon.

### Pull workflow

1. Choose an NSE ticker, optionally one outside the original portfolio.
2. For INFY, open a reproducible official-source case with eight evidence-backed lenses and a 4-quarter comparison.
3. For any other ticker, import or upload annual-report, quarterly-results and concall **primary** PDFs. Extract and index text using PyMuPDF and local SQLite.
4. The research engine chooses relevant source passages based on the investor's question or lens (business, financial, trajectory, balance, cash, narrative, guidance, bull/bear).
5. The UI displays passage plus issuer-document link and page; it does not silently fill gaps with general model knowledge. Optional model synthesis remains grounded in provided evidence.
6. Financial arithmetic is deterministic in `/api/results/compare` and the INFY case: always compare matched periods and basis, and leave missing metrics empty.

## 4. Questions the reviewer may ask (practice answers)

**Q. What is Push vs Pull?** Push proactively surfaces material changes and rule-triggered unusual EOD activity; Pull is investor-initiated research on companies grounded in their own disclosures.

**Q. Why not call this live stock data?** It is historical EOD quote/volume; exchange-wide streaming live data requires licensed feed and backend subscriptions. The date of the most recent trading session matters more than the page's last-refresh timestamp.

**Q. What is a corporate announcement?** A company disclosure submitted to NSE/BSE, such as results, management appointment, acquisition, rating action or dividend. The app opens original exchange filings for verification.

**Q. How is importance determined?** Type-specific business materiality and rule thresholds, not keyword frequency alone. M&A, results and executive departures typically earn earlier examination than compliance paperwork. We would calibrate thresholds using user feedback and disclosures, not train a black-box classifier on a tiny sample.

**Q. Describe the financial metrics.** Revenue is sales; EBITDA excludes interest, taxes, depreciation and amortisation; PBT is profit before tax; PAT is profit after tax. Operating profit can differ from EBITDA, and treating the two as synonyms is a common and important mistake.

**Q. QoQ vs YoY?** QoQ compares against the immediately preceding quarter; YoY compares against the same quarter one year earlier to reduce seasonality. Keep currency, entity and accounting basis consistent.

**Q. How do you explain management narrative vs numbers?** Identify a dated statement of management guidance, its horizon and accounting/currency metric, then compare with actual outcomes reported for the *same* horizon and basis. If the year is unfinished, mark guidance **pending**, not met or missed. At INFY Q2 FY27 the company reported INR-quarterly performance and FY27 constant-currency guidance; they cannot directly be scored against one another.

**Q. What are the eight analysis lenses?** Business snapshot, financial snapshot, trajectory, balance sheet, cash quality, narrative vs numbers, guidance and bull vs bear. Evidence is issuer-originated, and general ticker lenses are extractive when only uploaded PDFs are available.

**Q. How do you judge cash quality?** Compare cash from operations and free cash flow with net profit across periods and account for capex and working-capital changes. Profit without cash conversion can flag risk; one quarter is not enough to assert a trend.

**Q. How would you enrich a CFO resignation?** Use the official filing to identify the change and date, then source a verified biography from the issuer's leadership page or linked professional profile. Do not hallucinate jobs or dates. This prototype has PDF-background search, not a fully automated people-enrichment connector.

**Q. How many tickers does the app support?** The UI begins with 18 sample NSE stocks; the input parser generalises to any valid NSE ticker **where data is accessible**, currently limited to 30 concurrent watchlist items for free endpoint responsibility. The full exchange is much larger.

**Q. What does hypothetical/sample portfolio mean?** Example holdings in a mock portfolio, not connected to the user's broker. It calculates value from source quotes and P&L from the investor-provided *average buy price*. There is no portfolio balance without actual quotes; the app should show unknown, not zero.

**Q. What if NSE blocks requests from Render?** Return an error/empty state with provider label; keep source-backed historical research functioning. Production: licensed NSE/BSE data feed, scheduled ingestion, retries, durable stores and status observability.

**Q. Why optional AI?** The extraction and quantitative checks must be deterministic, explainable and cheap. LLM synthesis has value only over citations and source passages; a weaker answer based on general model memory is unacceptable for investments.

**Q. What are the limitations?** Inconsistent public provider access, no guaranteed BSE filing adapter, no background mobile pushes, no automatic bio enrichment, no automatic universal quarterly filing extraction, no authentication or durable document storage on free Render, and no brokerage trade execution.

## 5. Financial glossary quick reference

- **Annual report**: audited yearly primary business/financial statement, including notes and auditor qualifications.
- **Quarterly results**: company financial filing, more current but less detailed.
- **Concall transcript**: earnings call statements and analyst questions, used for explicit guidance.
- **Working-capital cycle**: time/cash tied in inventories and customer receivables less supplier payables.
- **FCF**: cash from operations minus capital expenditure; may differ from PAT.
- **D/E**: debt divided by equity; financial companies use different leverage conventions.
- **ROE/ROCE**: measures of return on shareholders' capital / employed capital.
- **Material event**: one potentially affecting investment assessment, not a promise the price will move.
- **Promoter pledge**: promoter uses shares as borrowing collateral.
- **Primary data**: direct issuer or exchange filings; **secondary** is another analyst's commentary and is disallowed for Pull in this challenge.

## 6. Demo checklist — things to avoid claiming

- **Do not** say a hosted public provider is guaranteed. Test the actual Render instance.
- **Do not** call source-backed INFY quarterly results a live price feed.
- **Do not** say EBITDA is reported when it isn't verified.
- **Do not** say FY27 management guidance was achieved in Oct 2026.
- **Do not** say the four ad-hoc companies have automatic complete research without PDFs.
- **Do not** say the sample holdings are a real linked demat portfolio.
- **Do not** call a four-minute client refresh a 24/7 push system.
- **Do** show one full workflow, one source click, one calculation and one clear limitation.

## 7. Product roadmap if asked

1. Licensed NSE/BSE feed with scheduled ingestion, robust retries and persistent event history.
2. Automatic issuer IR discovery for each ticker; reliable financial-statement table parsing and unit reconciliation.
3. Claim-to-outcome extraction pipeline: capture management statement, horizon, metric, source, then compare to a later filed result.
4. Opt-in notification channels and per-user notification materiality preferences.
5. Auth, encrypted document storage, retention policies, and a review/correction loop for disputed figures.
