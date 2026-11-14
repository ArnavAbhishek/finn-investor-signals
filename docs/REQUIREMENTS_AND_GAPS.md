# ENAM brief → implemented evidence → remaining limits

This checklist distinguishes **implemented software** from **tested end-to-end public data access**, which are not the same thing. ENAM emphasises judgment and a *thin-but-working* prototype rather than a long, broken feature list.

| Brief requirement | Implementation / testable route | Status and precise limitation |
|---|---|---|
| Mobile-first product that saves investor time | Overview, ranked feed, chart modal, source-first research, large touch actions | **Implemented**, tested at desktop 1440px and phone 390px |
| Push: filtered portfolio announcement digest; default last 24 h, adjustable window | `/api/digest`, 24h / 7d / 30d, search, material/routine display | **Implemented**. Actual incoming NSE filings subject to remote provider reachability |
| Push: priority/material-announcement categories | All **17** glossary categories, rules engine, dropdown filters | **Implemented** rules. Classification is heuristic and should be verified against original filing |
| Push: configurable price and unusual volume thresholds | `/api/prices`, `market_alerts`, ±% and volume multiple sliders | **Implemented** using available EOD data; automatic in-app checks, not 24/7 back-end push |
| Push: triggered notification | Browser Notification API for new priority verified filings | **Conditional**: permission required; page must be open, no background phone push service |
| Push: result-file first cut, Revenue, EBITDA, PBT, PAT with QoQ/YoY | INFY original fact sheets, Q2 FY27 vs Q1 FY27 vs Q2 FY26, `POST /api/results/compare` for supplied filing figures | **One real worked case + generic calculator**, not universal filing-PDF extraction. Source does not verify EBITDA, shown missing |
| Push: management-change professional background example | `/api/research/management` retrieves source paragraphs, filing → Research action | **Partial**. No automatic verified LinkedIn biography enrichment; no unsupported biographies |
| Prices/volume EOD for 15–20 portfolio companies | Starter 18 NSE companies; Yahoo data + NSE quote fallback | **Code implemented; third-party live access conditional** |
| Corporate announcements from NSE/BSE | NSE public website source | **NSE attempted**; BSE not implemented separately. NSE public endpoints may block hosting |
| Annual reports + concall transcripts from primary company sources | PDF import/upload, text extraction, local search, page citations; real Infosys case based on official documents | **Working PDF engine**. Automatic document harvesting from any ticker is not guaranteed |
| Mock portfolio 15–20 diverse listed firms | 18 starter entries, sector spread; editable watchlist | **Implemented**; mock means user-specified example holdings, not invested funds |
| Ad-hoc 3–5 firms outside portfolio | Quick choices HCLTECH, PIDILITIND, DIXON, DIVISLAB | **UI + ticker-general PDF workflow**, but real PDF libraries for all four are not preloaded |
| Research generalises beyond demo ticker | `validate_ticker`, arbitrary symbol PDF indexes and question search | **Implemented within available data**; insights require source PDFs |
| Pull: business snapshot | 8 lens endpoints, INFY evidence; arbitrary PDF retrieval | **Implemented for verified case; extractive for user-supplied PDFs** |
| Pull: financial snapshot | Same, INFY Q2 FY27 verified table | Same |
| Pull: trajectory | Interactive 4-quarter bar chart and linked fact sheets | Same; multi-year expansion needs document evidence |
| Pull: balance sheet | Official FY26 cash, investments and equity case; source excerpts for other issuers | Same, not automatically calculated for all firms |
| Pull: cash quality | FY26 FCF and conversion evidence with primary sources | Same |
| Pull: narrative vs actual numbers | INFY management comments vs reported growth, distinct currency basis and horizons | Same; careful interpretation rather than unsupported scoring |
| Pull: guidance | Infosys FY27 CC guidance shown as **pending outcome** | Same |
| Pull: bull vs bear | Two-sided documented evidence in INFY case | Same, not financial advice |
| UX interaction experimentation | Interactive cards, lens selectors, charts, alert rules, ticker exploration, filing-to-research transition | **Implemented** |
| Efficient build | Deterministic financial maths, cached public lookups, optional LLM synthesis | **Implemented** |
| Github + deployed mobile URL + genuine AI build history + email | ZIP, Dockerfile, render.yaml, README, prepared checklists and email draft | **NOT COMPLETE** until owner uploads and deploys; genuine share/export links must be supplied by owner |

## Why the scope is deliberately selective

ENAM explicitly calls the eight Pull outputs a *menu*, and the biography/quarterly comparison sections examples. Those examples are not individually mandatory for every ticker. FINN prioritises one trustworthy four-quarter source case, a general document retrieval engine, ranked filings and configurable EOD alerts over unsupported broad claims.

**Do not submit this as a 100% live NSE/BSE production integration.** The current public-provider network access cannot be guaranteed. Tell the evaluator exactly what works under source restrictions, what is sourced offline and which parts are roadmap work.
