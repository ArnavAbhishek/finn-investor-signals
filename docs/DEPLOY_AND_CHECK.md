# Deploy FINN v4 to GitHub + Render

Existing repo identified from the user's screenshots / connected GitHub metadata: `ArnavAbhishek/finn-investor-signals` and website `https://finn-investor-signals.onrender.com`. **This source ZIP has not been pushed to that repo or deployed.** The connected account did not grant this assistant repository push access.

## A. Update your GitHub repository (Linux)

**Recommended for your existing v1/v2/v3 deployment:**

```bash
cd ~/Downloads
unzip FINN_v4_ENAM_Submission.zip -d FINN-v4-unpacked
# The ZIP contains FINN/ as its root folder.
git clone https://github.com/ArnavAbhishek/finn-investor-signals.git finn-repo
cp -a FINN-v4-unpacked/FINN/. finn-repo/
cd finn-repo
# Optional: remove any obsolete v1/v2/v3 files no longer used.
git status
# Inspect README and ensure Dockerfile and app/ are at repository top level.
git add -A
git commit -m "Build FINN source-first Push Pull research v4"
git push origin main
```

If GitHub prompts for credentials, authenticate using GitHub Desktop, `gh auth login`, or an appropriate credential manager. Don't put a token into committed files. If you cannot use the terminal, create/modify the repository via GitHub's upload interface and ensure the ZIP itself is not the only uploaded item.

## B. Deploy on Render

1. Go to https://dashboard.render.com and open the existing **finn-investor-signals** web service.
2. Settings → ensure it points to GitHub branch `main` with `Docker` runtime, root directory blank, Dockerfile path `./Dockerfile`, health check `/api/health`.
3. Choose a free plan if appropriate. In the **Environment** tab, add `FINN_DATA_DIR=/tmp/finn_data` (or keep the existing setting). Do not expose the API key to frontend JS.
4. Turn on **Auto Deploy**, or manually select **Deploy latest commit**.
5. Watch the logs until the deployment is healthy. New static assets (`/assets/finn4.js`, `/assets/finn4.css`) should be served.
6. Visit `https://finn-investor-signals.onrender.com/api/health`. A successful v4 deployment returns `"version":"4.0.0"`. If it still says 3.0.0 or 2.0.0, Render has not updated the code.

No separate Vercel/Netlify service is required: FastAPI serves the UI and API from the same origin.

## C. Live URL reviewer testing

**Do these on the actual deployed Render URL**, not just localhost. The evaluator needs to see a working phone UI and source-aware failure states.

- [ ] `/api/health` returns `ok: true`, `version: 4.0.0`.
- [ ] `/api/case/INFY` returns `kind: verified_historical_case`, 4 quarters, eight lenses, issuer source links. This route should work without NSE/Yahoo access.
- [ ] `/api/research/angles?ticker=INFY&angle=narrative` returns two cited paragraphs.
- [ ] `/api/research/angles?ticker=DIXON&angle=business` reports missing source PDFs until genuine documents are indexed.
- [ ] Home → **Explore the evidence** opens INFY source research.
- [ ] Research → eight lens tabs switch results and source links.
- [ ] Research → Revenue, Operating profit, PBT and PAT buttons change the four-quarter chart.
- [ ] Research → Q2 results table shows actual QoQ/YoY and **EBITDA: Not verified**.
- [ ] At phone width, no horizontal overflow or cut-off research cards.
- [ ] Watchlist → add or remove a ticker; open stock; choose 1D, 3M, 6M and note source/unavailable state.
- [ ] Portfolio → edit shares and purchase price; calculation changes if a verified market quote is present.
- [ ] Signals → category filter and time-window buttons work; original exchange URL if filings were received.
- [ ] Change EOD alert thresholds; choose **Recheck now**. Recheck must invalidate cache; second rapid press should explain rate limiting.
- [ ] Open the URL in an incognito/private browser without GitHub or Render login.
- [ ] Verify visible source labels and whether market feeds actually work **from Render**.

## D. Public data restrictions — what to say

The UI automatically rechecks every ~4 minutes while open; manual Recheck invalidates caches. **This is EOD market intelligence, not streaming**; closing the tab stops browser-side polling. Yahoo's chart endpoints and the publicly available NSE website can throttle/block cloud addresses. If live market data fails, show the source limitation honestly. The verified Infosys historical case still works and remains tied to official issuer documents.

A production path would use licensed NSE/BSE market-data integrations, a scheduled server-side data worker, a durable database and background notification service. Neither enterprise exchange licence nor paid API credentials are part of this free-tier challenge prototype.

## E. Optional LLM synthesis

- The source-search and casebook work **without** an API key.
- To activate optional evidence-grounded model synthesis, set a secret `OPENAI_API_KEY` in Render's Environment settings and `FINN_OPENAI_MODEL` appropriately. The free version is safer without it because this public prototype has no authentication or usage quota.
- Never paste API keys into GitHub, URLs, console screenshots or the frontend.

## F. Debugging

- **Old UI**: Check repo branch, Dockerfile path, Render deployment SHA, browser hard refresh and `/api/health` version.
- **503 from `/api/chart`**: cloud market provider blocked or timed out. The UI must show source failure, not a fabricated line.
- **Missing INFY case**: verify new `app/services/casebook.py`, `app/services/angles.py` and `/assets/finn4.js` were uploaded.
- **Research upload lost**: free Render filesystem is ephemeral; index PDFs again, or use a persistent storage backend for production.
- **Blank app**: browser console check, review Render logs; run `node --check` and Python tests locally.
- **Notifications missing**: request permission on HTTPS; many browsers require user interaction and will not notify when the page is closed.

## G. Tests before sending

```bash
python -m pytest -q
node --check app/static/app.js
node --check app/static/finn4.js
curl -s https://finn-investor-signals.onrender.com/api/health
curl -s https://finn-investor-signals.onrender.com/api/case/INFY
```

Keep screenshots of actual Render runs and a short screen recording showing the critical Push/Pull workflows. Do not send the submission before the live URL is verified.

**Automated deployment smoke check:** Run `python scripts/verify_deployment.py --base https://finn-investor-signals.onrender.com` after deployment. The script verifies health, starter watchlist and historical research even if live public price data is blocked.
