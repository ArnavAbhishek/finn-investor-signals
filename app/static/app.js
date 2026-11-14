/* FINN v3 — a deliberately focused investor workspace. No invented live market values. */
'use strict';
const $ = id => document.getElementById(id);
const qsa = selector => [...document.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const stored = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
const fmtMoney = (n, digits=2) => Number.isFinite(Number(n)) ? `₹${new Intl.NumberFormat('en-IN', {minimumFractionDigits:digits, maximumFractionDigits:digits}).format(+n)}` : '—';
const fmtCompact = n => !Number.isFinite(n) ? '—' : n>=1e7 ? '₹'+(n/1e7).toFixed(2)+' Cr' : n>=1e5 ? '₹'+(n/1e5).toFixed(2)+' L' : fmtMoney(n,0);
const fmtPercent = n => Number.isFinite(Number(n)) && n!==null ? `${n >= 0 ? '+' : ''}${(+n).toFixed(2)}%` : '—';
const direction = n => n==null?'neutral':n>=0?'up':'down';
const validSymbol = x => /^[A-Z0-9&._-]{1,20}$/.test(String(x || ''));
const sign = n => (n >= 0 ? '+' : '−');
const readable = (d) => { try { return new Date(d).toLocaleDateString('en-IN', {day:'numeric',month:'short',timeZone:'Asia/Kolkata'}); } catch {return '—';} };
const starterHoldings = [
  {symbol:'RELIANCE', quantity:10, average:1260},
  {symbol:'TCS', quantity:5, average:3330},
  {symbol:'HDFCBANK', quantity:12, average:1080},
  {symbol:'ICICIBANK', quantity:10, average:1300},
];
const palette = ['#199a73','#4d80c7','#ac79cb','#e2aa4c','#5eb8b0','#e17b73','#899cc1','#b3aa69'];
const categoryLabels = {results:'Results','M&A':'M&A',fund_raise:'Fund raising',management_change:'Leadership',litigation:'Litigation',insider_trading:'Insider activity',earnings_call:'Earnings call',investor_meetings:'Investor meeting',credit_rating:'Credit rating',dividend:'Dividend',bonus_split:'Bonus / split',capex:'Capex',press_release:'Company update',postal_ballot:'Postal ballot',agm_egm:'AGM / EGM',pledging:'Pledging',unclassified:'Routine'};
const state = {
  preview: new URLSearchParams(location.search).get('preview') === '1',
  companies: [], watchlist: [], prices: [], filings: [], alerts: [],
  holdings: stored('finn3_holdings', starterHoldings), customized: stored('finn3_customized',false),
  storedWatchlist: stored('finn3_watchlist',null), hours: stored('finn3_hours',24),
  priceRule: stored('finn3_priceRule',3), volumeRule: stored('finn3_volumeRule',2),
  page: 'overview', search: '', sector: 'All', stock: null, chartPeriod:'3M',
  refreshToken:0, chartToken:0, updatedAt:null, statusWarnings:[], activeRequest:false, editing:null,
};
let toastTimer;
function toast(message) {const node=$('toast');node.textContent=message;node.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>node.classList.remove('show'),4500);}
function persist() {
  try { localStorage.setItem('finn3_watchlist',JSON.stringify(state.watchlist));
  localStorage.setItem('finn3_holdings',JSON.stringify(state.holdings));
  localStorage.setItem('finn3_customized',JSON.stringify(state.customized));
  localStorage.setItem('finn3_hours',JSON.stringify(state.hours));
  localStorage.setItem('finn3_priceRule',JSON.stringify(state.priceRule));
  localStorage.setItem('finn3_volumeRule',JSON.stringify(state.volumeRule));
  } catch { /* Browser privacy mode may deny storage; in-memory state still works. */ }
}
async function api(url, options={}) {
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),40000);
  try { const r=await fetch(url,{...options,signal:controller.signal,cache:'no-store'});const value=await r.json().catch(()=>({}));if(!r.ok) throw Error(value.detail || `Request failed (${r.status})`);return value; }
  catch(err) {if(err.name==='AbortError')throw Error('Data request timed out');throw err;}
  finally{clearTimeout(timeout)}
}
const meta = symbol => state.companies.find(x=>x.symbol===symbol) || {symbol,name:symbol,sector:'Unclassified'};
const quotes = () => Object.fromEntries(state.prices.map(p=>[p.symbol,p]));
const companySymbols = () => [...new Set([...state.watchlist.map(x=>x.symbol), ...state.holdings.map(x=>x.symbol)])].slice(0,30);
const tickerUrl = symbol => `https://www.nseindia.com/get-quotes/equity?symbol=${encodeURIComponent(symbol)}`;
function setPage(page) {
  if(!['overview','watchlist','portfolio','signals','research'].includes(page))return;
  state.page=page;
  qsa('.page').forEach(x=>x.classList.toggle('visible',x.id===`page-${page}`));
  qsa('[data-nav]').forEach(x=>{x.classList.toggle('selected',x.dataset.nav===page);if(x.dataset.nav===page)x.setAttribute('aria-current','page');else x.removeAttribute('aria-current')});
  $('pageLabel').textContent=({overview:'Overview',watchlist:'Watchlist',portfolio:'Portfolio',signals:'Signals',research:'Research'})[page];
  if(page==='research')loadResearchDocuments();
  window.scrollTo({top:0,behavior:'instant'});
  history.replaceState({},'',`${location.pathname}${location.search}#${page}`);
}
function overlay(id,open=true){$(id).classList.toggle('open',open);$(id).setAttribute('aria-hidden',String(!open));document.body.style.overflow=qsa('.overlay.open').length?'hidden':'';}
function updatedLabel(){return state.updatedAt ? `Checked ${state.updatedAt.toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit',timeZone:'Asia/Kolkata'})} · auto 4 min` : 'Checking sources…';}
function renderStatus(loading=false){
  const status=$('statusLine'), label=$('statusText'), mode=state.preview?'Illustrative preview':'Historical EOD';
  status.className='status-line';
  if(loading){label.textContent='Checking public market sources and NSE filings…';}
  else if(state.preview){label.textContent='Illustrative preview — fictional prices and announcements';status.classList.add('problem');}
  else if(state.statusWarnings.length){label.textContent='Some public sources are unavailable · available data only';status.classList.add('problem');}
  else {label.textContent=`${mode} · Auto-check every 4 minutes`;status.classList.add('ok');}
  $('updateLabel').textContent=updatedLabel();
  $('infoWarnings').textContent=state.statusWarnings.length ? state.statusWarnings.join(' · ') : 'No provider errors reported in the last check.';
}
function updateCurrentSession(){
  const dates=state.prices.map(x=>String(x.date||'').slice(0,10)).filter(x=>/^\d{4}-\d{2}-\d{2}$/.test(x));
  const recent=dates.sort().at(-1);
  $('sessionTag').textContent=state.preview?'PREVIEW ONLY':recent?`${readable(recent)} EOD`:'EOD source pending';
  $('dateCaption').textContent=new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long',timeZone:'Asia/Kolkata'}).toUpperCase()+'  /  INVESTOR DESK';
}
function renderOverview(){
  updateCurrentSession();$('pulseFoot').textContent=state.preview?'Illustrative fixtures only · no actual market records are implied.':'Latest available EOD records, not streaming quotes.';const pmap=quotes();const active=state.watchlist.map(x=>pmap[x.symbol]).filter(x=>x&&x.change_pct!=null);
  const up=active.filter(x=>x.change_pct>0).length,down=active.filter(x=>x.change_pct<0).length,flat=active.length-up-down;
  const viewed=active.length;
  $('pulseCard').classList.toggle('down',down>up);
  $('breadthNumber').textContent=viewed ? `${Math.round(up/viewed*100)}%` : '—';
  $('breadthDescription').textContent=viewed ? `${up} of ${viewed} stocks advanced${flat?' · '+flat+' unchanged':''}` : 'No verified price changes returned';
  $('breadthBar').style.width=(viewed ? up/viewed*100 : 0)+'%';
  $('upCount').textContent=up;$('downCount').textContent=down;$('dataCount').textContent=viewed;
  const sorted=[...active].sort((a,b)=>Math.abs(b.change_pct)-Math.abs(a.change_pct)).slice(0,3);
  $('moversList').innerHTML=sorted.length ? sorted.map(x=>`<button class="mover-item" data-stock="${escapeHTML(x.symbol)}"><span class="mover-label"><span class="ticker-avatar">${escapeHTML(x.symbol.slice(0,2))}</span><span><strong>${escapeHTML(x.symbol)}</strong><small>${escapeHTML(meta(x.symbol).name)}</small></span></span><span class="mover-numbers"><strong class="${direction(x.change_pct)}">${fmtPercent(x.change_pct)}</strong><small>${fmtMoney(x.close)}</small></span></button>`).join('') : `<div class="empty-simple">Market movers will appear when verified prices arrive.</div>`;
  const watch=state.watchlist.slice(0,4);
  $('overviewStocks').innerHTML=watch.map(c=>{const p=pmap[c.symbol];return `<button class="stock-tile" data-stock="${escapeHTML(c.symbol)}"><span class="tile-ticker">${escapeHTML(c.symbol)}</span><span class="tile-name">${escapeHTML(c.name)}</span><span class="tile-price">${p?fmtMoney(p.close):'—'}</span><span class="tile-move ${direction(p?.change_pct)}">${p?fmtPercent(p.change_pct):'Awaiting price'}</span></button>`}).join('') || '<p class="empty-simple">Add stocks to your watchlist.</p>';
  const focus=state.filings.filter(f=>f.tier==='high').slice(0,2);
  const fallbackAlerts=state.alerts.slice(0,2);
  $('overviewSignals').innerHTML=focus.length ? focus.map(f=>`<button class="signal-tease" data-signals="${escapeHTML(f.symbol)}"><span class="signal-icon">✳</span><span class="signal-tease-main"><strong>${escapeHTML(f.demo?f.title.replace(/^Illustrative scenario:\s*/i,''):f.title)}</strong><small>${escapeHTML(f.symbol)} · ${escapeHTML(categoryLabels[f.category]||f.category)} ${f.demo?'· EXAMPLE':''}</small></span><span>↗</span></button>`).join('') : fallbackAlerts.length?fallbackAlerts.map(x=>`<button class="signal-tease" data-stock="${escapeHTML(x.symbol)}"><span class="signal-icon">◈</span><span class="signal-tease-main"><strong>${escapeHTML(x.symbol)} · unusual recorded move</strong><small>Price / volume crossed your threshold</small></span><span>↗</span></button>`).join('') : `<div class="empty-simple">No high-priority triggers in this window. Check a longer period in Signals.</div>`;
  const sum=portfolioTotals();$('previewLabel').textContent=state.customized?'Your holdings · saved here':'Sample holdings · editable';
  $('previewValue').textContent=sum.known?fmtCompact(sum.value):'—';
  $('previewReturn').textContent=sum.known?(sum.missing?`${sum.missing} unpriced · partial valuation`: `${fmtPercent(sum.returnPct)} based on purchase prices`):'Add holdings and connect prices to begin';
  wireStockButtons();qsa('[data-signals]').forEach(b=>b.onclick=()=>{$('signalSearch').value=b.dataset.signals;setPage('signals');renderSignals()});
}
function renderSectorFilters(){
  const sectors=['All',...new Set(state.watchlist.map(c=>c.sector||'Unclassified'))];
  if(!sectors.includes(state.sector))state.sector='All';
  $('watchSectors').innerHTML=sectors.map(s=>`<button type="button" class="${s===state.sector?'selected':''}" data-sector="${escapeHTML(s)}">${escapeHTML(s)}</button>`).join('');
  qsa('[data-sector]').forEach(btn=>btn.onclick=()=>{state.sector=btn.dataset.sector;renderWatchlist()});
}
function renderWatchlist(){
  renderSectorFilters();const search=$('stockSearch').value.toLowerCase().trim();const current=state.watchlist.filter(c=>(state.sector==='All'||c.sector===state.sector)&&`${c.symbol} ${c.name} ${c.sector}`.toLowerCase().includes(search));const pmap=quotes();
  $('watchlistCount').textContent=`${current.length} shown · ${state.watchlist.length} followed · NSE has far more stocks than this starter list`;
  $('watchlistRows').innerHTML=current.map(c=>{const p=pmap[c.symbol];return `<div class="watch-row-wrap" style="position:relative;min-width:0"><button type="button" class="watch-row" style="width:100%" data-stock="${escapeHTML(c.symbol)}"><span class="ticker-avatar">${escapeHTML(c.symbol.slice(0,2))}</span><span class="watch-row-text"><strong>${escapeHTML(c.symbol)}</strong><small>${escapeHTML(c.name)} · ${escapeHTML(c.sector)}</small></span><span class="watch-row-price"><b>${p?fmtMoney(p.close):'—'}</b><span class="${direction(p?.change_pct)}">${p?fmtPercent(p.change_pct):'No quote'}</span></span></button><button type="button" class="watch-remove" data-remove="${escapeHTML(c.symbol)}" style="position:absolute;right:3px;top:2px" aria-label="Remove ${escapeHTML(c.symbol)} from watchlist" title="Remove from watchlist">×</button></div>`}).join('')||'<div class="empty-state">No matching stocks. Add an NSE ticker or clear your search.</div>';
  wireStockButtons();qsa('[data-remove]').forEach(btn=>btn.onclick=()=>{state.watchlist=state.watchlist.filter(c=>c.symbol!==btn.dataset.remove);persist();renderWatchlist();renderOverview();toast(`${btn.dataset.remove} removed from watchlist`)});
}
function portfolioTotals(){
  const pmap=quotes();let value=0,spent=0,allSpent=0,priced=0;const sectors={};
  for(const h of state.holdings){const cost=(+h.quantity)*(+h.average),p=pmap[h.symbol];allSpent+=cost;
    if(!p||!Number.isFinite(+p.close)||+p.close<=0)continue;
    const val=(+h.quantity)*(+p.close);value+=val;spent+=cost;priced++;
    const sector=meta(h.symbol).sector||'Unclassified';sectors[sector]=(sectors[sector]||0)+val;
  }
  return {value,spent,allSpent,priced,known:priced>0,missing:state.holdings.length-priced,sectors,
          gain:value-spent,returnPct:spent>0?(value/spent-1)*100:null};
}
function renderPortfolio(){
  const t=portfolioTotals(),pmap=quotes();
  $('portfolioKind').textContent=state.customized?'Your positions · saved on this browser only':'Sample portfolio · edit, remove or replace any position';
  $('totalPortfolioValue').textContent=t.known?fmtCompact(t.value):'—';
  $('totalInvested').textContent=fmtCompact(t.allSpent);
  $('totalGain').textContent=t.known?`${sign(t.gain)}${fmtCompact(Math.abs(t.gain))}`:'—';
  $('totalGain').className=t.known?direction(t.gain):'';
  $('gainPct').textContent=t.known?fmtPercent(t.returnPct)+' on priced holdings':'Unavailable until EOD records load';
  $('portfolioStamp').textContent=t.missing?`${t.priced} of ${state.holdings.length} positions priced · incomplete value`:'Latest available EOD valuation';
  $('holdingCount').textContent=String(state.holdings.length);
  $('holdingsRows').innerHTML=state.holdings.length?state.holdings.map(h=>{const p=pmap[h.symbol];const value=p?(+h.quantity)*(+p.close):null;const profit=p?(value-(+h.quantity)*(+h.average)):null;
    return `<div class="holding-row"><span class="ticker-avatar">${escapeHTML(h.symbol.slice(0,2))}</span><span class="holding-symbol"><b>${escapeHTML(h.symbol)}</b><small>${h.quantity} shares · buy ${fmtMoney(h.average)}</small></span><span class="holding-pos"><b>${value==null?'—':fmtMoney(value,0)}</b><small class="${direction(profit)}">${profit==null?'Price unavailable':`${sign(profit)}${fmtMoney(Math.abs(profit),0)}`}</small></span><button class="small-icon-button" data-edit="${escapeHTML(h.symbol)}" type="button" aria-label="Edit ${escapeHTML(h.symbol)}">✎</button></div>`}).join(''):'<div class="empty-state">No holdings yet. Add a stock to start tracking a portfolio.</div>';
  qsa('[data-edit]').forEach(b=>b.onclick=()=>openHolding(b.dataset.edit));
  const sectors=Object.entries(t.sectors).sort((a,b)=>b[1]-a[1]);let cumulative=0;let stops=[];
  if(t.value>0){for(let i=0;i<sectors.length;i++){const slice=sectors[i][1]/t.value*100;stops.push(`${palette[i%palette.length]} ${cumulative}% ${cumulative+slice}%`);cumulative+=slice}}
  $('sectorDonut').style.background=stops.length?`conic-gradient(${stops.join(',')})`:'conic-gradient(#edf3ef 0% 100%)';
  $('sectorCount').textContent=sectors.length;
  $('sectorLegend').innerHTML=sectors.map(([name,value],i)=>`<div class="sector-line"><span><i class="sector-dot" style="background:${palette[i%palette.length]}"></i>${escapeHTML(name)}</span><b>${(100*value/t.value).toFixed(0)}%</b></div>`).join('')||'<div class="empty-simple">Valuation needed for allocation.</div>';
}
function renderSignals(){
  const word=$('signalSearch').value.toLowerCase().trim();const routine=$('showRoutine').checked;
  qsa('[data-hours]').forEach(b=>b.classList.toggle('selected',+b.dataset.hours===state.hours));
  $('moveRule').value=state.priceRule;$('volumeRule').value=state.volumeRule;
  $('moveRuleValue').textContent=`±${(+state.priceRule).toFixed(1)}%`;$('volumeRuleValue').textContent=`${(+state.volumeRule).toFixed(1)}×`;
  $('feedSource').textContent=state.preview?'Preview scenarios':'Official NSE filings · best effort';
  const categoryFilter=$('filingCategory')?.value||'all';
  const filings=state.filings.filter(x=>(categoryFilter==='all'||x.category===categoryFilter)&&(routine||x.tier!=='routine')&&(!word||`${x.symbol} ${x.title} ${x.category} ${x.detail}`.toLowerCase().includes(word)));
  $('filingCount').textContent=filings.length;$('navSignalCount').textContent=state.filings.filter(x=>x.tier==='high').length;
  $('navSignalCount').hidden=!state.filings.some(x=>x.tier==='high');
  $('filingsFeed').innerHTML=filings.length?filings.map((f,i)=>`<article class="filing" data-filing="${i}"><button type="button" class="filing-button" aria-expanded="false"><span class="filing-bubble ${f.tier==='high'?'high':''}">✳</span><span class="filing-content"><span class="filing-meta"><b>${escapeHTML(f.symbol)}</b><span>${escapeHTML(categoryLabels[f.category]||f.category)}</span><span>${f.demo?'FICTIONAL':readable(f.published_at)}</span></span><span class="filing-title">${escapeHTML(f.title)}</span><span class="filing-why">${escapeHTML(f.why||'Review the original source filing.')}</span></span><span class="filing-caret">⌄</span></button><div class="filing-more">${escapeHTML(f.detail||'No source description provided.')}<div>${f.source_url&&!f.demo?`<a href="${escapeHTML(f.source_url)}" target="_blank" rel="noopener">Open exchange filing ↗</a>`:'<span class="subtle">Illustrative scenario — no exchange filing claimed.</span>'} <button type="button" class="filing-research" data-ticker="${escapeHTML(f.symbol)}">Investigate company ↗</button></div></div></article>`).join(''):
    `<div class="empty-state">${state.preview?'No sample filings in this window.':'No matching verified filings returned. NSE access may be restricted; try 7 or 30 days.'}</div>`;
  qsa('.filing-button').forEach(btn=>btn.onclick=()=>{const article=btn.closest('.filing');article.classList.toggle('expanded');btn.setAttribute('aria-expanded',String(article.classList.contains('expanded')))});
  qsa('.filing-research').forEach(btn=>btn.onclick=()=>{if(typeof activateTicker==='function')activateTicker(btn.dataset.ticker);else{setPage('research');$('researchSymbol').value=btn.dataset.ticker;loadResearchDocuments();}});
  $('alertCount').textContent=state.alerts.length;
  const pmap=quotes();$('alertRows').innerHTML=state.alerts.length?state.alerts.slice(0,14).map(a=>{const p=pmap[a.symbol];return `<button type="button" class="alert-item" data-stock="${escapeHTML(a.symbol)}"><div><strong>${escapeHTML(a.symbol)}</strong><span>${p?.volume_ratio!=null?`${p.volume_ratio.toFixed(2)}× usual volume`:'EOD movement trigger'}</span></div><strong class="${direction(p?.change_pct)}">${fmtPercent(p?.change_pct)}</strong></button>`}).join(''):'<div class="empty-simple">Nothing crosses your thresholds in available EOD data.</div>';
  wireStockButtons();
}
function renderAll(){renderStatus();renderOverview();renderWatchlist();renderPortfolio();renderSignals()}
async function refreshData({force=false, quiet=false}={}){
  if(state.activeRequest)return;
  state.activeRequest=true;const id=++state.refreshToken;
  if(force){$('refreshBtn').classList.add('busy');$('refreshBtn').disabled=true;$('refreshBtn').querySelector('span').textContent='Rechecking…';}
  if(!quiet)renderStatus(true);
  try{
    if(force){const verdict=await api('/api/refresh',{method:'POST'});if(!verdict.accepted)toast(`Recheck limited: try again in ${verdict.retry_after_seconds}s. Showing recent results.`);}
    const symbols=companySymbols();
    if(!symbols.length){state.prices=[];state.filings=[];state.alerts=[];state.statusWarnings=[];state.updatedAt=new Date();renderAll();return;}
    const priceQuery=new URLSearchParams({mode:state.preview?'demo':'live',symbols:symbols.join(','),price_threshold:String(state.priceRule),volume_threshold:String(state.volumeRule)});
    const filingQuery=new URLSearchParams({mode:state.preview?'demo':'live',symbols:symbols.join(','),hours:String(state.hours)});
    const [priceResult,filingResult]=await Promise.allSettled([api('/api/prices?'+priceQuery),api('/api/digest?'+filingQuery)]);
    if(id!==state.refreshToken)return;
    const warning=[];
    if(priceResult.status==='fulfilled'){
      const incoming=priceResult.value.items||[];
      if(incoming.length || !state.prices.length || state.preview){state.prices=incoming;state.alerts=priceResult.value.alerts||[];}
      else warning.push('Price provider failed; retaining last successfully returned EOD records until newer verified data arrives.');
      if(priceResult.value.warning)warning.push(priceResult.value.warning);
    }else warning.push('Market prices: '+priceResult.reason.message);
    const oldPriority = new Set(state.filings.filter(x=>x.tier==='high').map(x=>x.id || [x.symbol,x.title,x.published_at].join('|')));
    const hadPriorCheck=Boolean(state.updatedAt);
    if(filingResult.status==='fulfilled'){
      state.filings=filingResult.value.items||[];
      if(filingResult.value.warning)warning.push(filingResult.value.warning);
    }else warning.push('Corporate filings: '+filingResult.reason.message);
    const newPriority = hadPriorCheck ? state.filings.filter(x=>x.tier==='high'&&!oldPriority.has(x.id || [x.symbol,x.title,x.published_at].join('|'))) : [];
    state.statusWarnings=warning;state.updatedAt=new Date();renderAll();
    if(newPriority.length && !force && !state.preview){ toast(`${newPriority.length} new priority filing${newPriority.length===1?'':'s'} in your watchlist`); if(typeof notifyPriorityFilings==='function')notifyPriorityFilings(newPriority); }
    if(state.stock)loadStockChart(state.stock);
    if(force)toast(warning.length?'Recheck finished; see source details for unavailable feeds.':'Source recheck completed.');
  }catch(err){state.statusWarnings=[err.message];renderStatus();toast(err.message);}
  finally{state.activeRequest=false;$('refreshBtn').classList.remove('busy');$('refreshBtn').disabled=false;$('refreshBtn').querySelector('span').textContent='Recheck now';}
}
function wireStockButtons(){qsa('[data-stock]').forEach(button=>button.onclick=()=>openStock(button.dataset.stock));}
function chartMarkup(points,period){
  const filtered=points.filter(x=>Number.isFinite(+x.close)&&+x.close>0);
  if(filtered.length<2) return '<div class="empty-state">No usable chart points for this period.</div>';
  const prices=filtered.map(x=>+x.close), lo=Math.min(...prices),hi=Math.max(...prices),diff=hi-lo||1;
  const mobile=window.innerWidth<760;const W=mobile?380:800,H=mobile?252:270,L=mobile?10:16,R=mobile?58:78,T=mobile?22:23,B=35,plotW=W-L-R,plotH=H-T-B;
  const pos=(v,i)=>[L+i/(prices.length-1)*plotW,T+(hi-v)/diff*plotH];
  const pointsLine=prices.map((v,i)=>pos(v,i).map(x=>x.toFixed(2)).join(',')).join(' ');
  const area=`M${L},${H-B} L${prices.map((v,i)=>pos(v,i).map(x=>x.toFixed(2)).join(',')).join(' L')} L${W-R},${H-B}Z`;
  const inc=prices.at(-1)>=prices[0],accent=inc?'#16a378':'#d75f58', color=inc?'#1da976':'#e77a6d';
  const uid='c'+Math.floor(Math.random()*1e8);
  let grid='';for(let i=0;i<4;i++){const y=T+i*plotH/3;const label=hi-i*diff/3;grid+=`<line x1="${L}" y1="${y}" x2="${W-R}" y2="${y}" stroke="#e3ece8" stroke-dasharray="4 6"/><text x="${W-R+7}" y="${y+4}" fill="#8da0a1" font-size="${mobile?13:14}">${Math.round(label).toLocaleString('en-IN')}</text>`;}
  const dates=[filtered[0],filtered[Math.floor(filtered.length/2)],filtered.at(-1)];
  const dateText=d=>period==='1D'?new Date(d.date).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kolkata'}):readable(d.date);
  const markers=dates.map((d,i)=>`<text x="${L+i*plotW/2}" y="${H-8}" fill="#8a9a9c" font-size="${mobile?13:14}" text-anchor="${i===0?'start':i===2?'end':'middle'}">${escapeHTML(dateText(d))}</text>`).join('');
  return `<div class="chart-tooltip" id="hoverPoint">${fmtMoney(prices.at(-1))} · ${escapeHTML(dateText(filtered.at(-1)))}</div><svg class="price-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="${period} verified price history"><defs><linearGradient id="${uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${color}" stop-opacity=".25"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs>${grid}<path d="${area}" fill="url(#${uid})"/><polyline points="${pointsLine}" fill="none" stroke="${accent}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>${markers}<line class="cursor-line" x1="0" x2="0" y1="${T}" y2="${H-B}" stroke="#6daca0" stroke-dasharray="4 5" visibility="hidden"/><circle class="cursor-dot" cx="0" cy="0" r="5" fill="${accent}" stroke="white" stroke-width="3" visibility="hidden"/><rect class="chart-surface" x="${L}" y="${T}" width="${plotW}" height="${plotH}" fill="transparent" style="cursor:crosshair"/></svg>`;
}
function makeChartInteractive(box,points,period){
  const svg=box.querySelector('.price-svg');if(!svg)return;
  const line=svg.querySelector('.cursor-line'),dot=svg.querySelector('.cursor-dot'),tip=box.querySelector('#hoverPoint');
  const good=points.filter(x=>Number.isFinite(+x.close)&&+x.close>0);const prices=good.map(x=>+x.close),lo=Math.min(...prices),hi=Math.max(...prices),spread=hi-lo||1;const mobile=svg.viewBox.baseVal.width<500;const W=svg.viewBox.baseVal.width,H=svg.viewBox.baseVal.height,L=mobile?10:16,R=mobile?58:78,T=mobile?22:23,B=35;
  svg.addEventListener('pointermove',e=>{
    const rect=svg.getBoundingClientRect();const x=(e.clientX-rect.left)/rect.width*W;
    const index=Math.round(Math.max(0,Math.min(1,(x-L)/(W-L-R)))*(good.length-1));
    const xx=L+index/(good.length-1)*(W-L-R),yy=T+(hi-prices[index])/spread*(H-T-B);
    line.setAttribute('x1',xx);line.setAttribute('x2',xx);line.setAttribute('visibility','visible');dot.setAttribute('cx',xx);dot.setAttribute('cy',yy);dot.setAttribute('visibility','visible');
    const date=period==='1D'?new Date(good[index].date).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kolkata'}):readable(good[index].date);
    tip.textContent=`${fmtMoney(prices[index])} · ${date}`;
  });
  svg.addEventListener('pointerleave',()=>{line.setAttribute('visibility','hidden');dot.setAttribute('visibility','hidden');});
}
function tvFallback(symbol,reason){
  const url=`https://www.tradingview.com/symbols/NSE-${encodeURIComponent(symbol)}/`;
  return `<div class="chart-fallback"><strong>Historical API unavailable on this server</strong><p>${escapeHTML(reason)}. An independently hosted chart is shown below if your browser permits it. This is third-party market data, not invented prices.</p><div id="tradingviewMount" style="height:345px;width:100%;background:#fff"></div><a href="${url}" target="_blank" rel="noopener">Open NSE:${escapeHTML(symbol)} on TradingView ↗</a></div>`;
}
function attachTradingView(symbol){
  const container=$('tradingviewMount');if(!container)return;
  container.innerHTML='<div class="tradingview-widget-container" style="height:100%;width:100%"><div class="tradingview-widget-container__widget" style="height:calc(100% - 28px);width:100%"></div><div class="tradingview-widget-copyright" style="font-size:11px;color:#71878b">Charts supplied by TradingView · Third-party data</div></div>';
  const script=document.createElement('script');script.type='text/javascript';script.async=true;script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
  script.textContent=JSON.stringify({autosize:true,symbol:`NSE:${symbol}`,interval:state.chartPeriod==='1D'?'5':'D',timezone:'Asia/Kolkata',theme:'light',style:'3',locale:'en',backgroundColor:'#ffffff',gridColor:'rgba(37,75,62,0.08)',allow_symbol_change:false,hide_top_toolbar:true,hide_side_toolbar:true,withdateranges:true,details:false,calendar:false,save_image:false,watchlist:[],support_host:'https://www.tradingview.com'});
  container.firstElementChild.appendChild(script);
}
async function loadStockChart(symbol){
  const id=++state.chartToken,period=state.chartPeriod;const stage=$('stockChartStage');if(!stage)return;
  stage.innerHTML='<div class="skeleton-line" style="height:220px"></div>';$('chartSourceNote').textContent='Fetching historical observations…';
  try{
    const data=await api('/api/chart?'+new URLSearchParams({symbol,period,mode:state.preview?'demo':'live'}));
    if(id!==state.chartToken||state.stock!==symbol)return;
    stage.innerHTML=chartMarkup(data.points,period);makeChartInteractive(stage,data.points,period);
    $('chartSourceNote').textContent=`${data.source} · ${data.updated_at?'last record '+readable(data.updated_at):'synthetic preview'} · ${data.warning||''}`;
    if(data.close!=null){$('detailPrice').textContent=fmtMoney(data.close);}
  }catch(err){if(id!==state.chartToken||state.stock!==symbol)return;if(state.preview){stage.innerHTML='<div class="empty-state">This newly added stock has no fictional preview history. Open the normal workspace to request its actual historical records.</div>';$('chartSourceNote').textContent='Preview fixtures are intentionally limited; no fabricated prices have been added for this symbol.';return;}stage.innerHTML=tvFallback(symbol,err.message);$('chartSourceNote').textContent='Historical host endpoint unavailable. Fallback widget provided by TradingView (availability depends on browser access).';attachTradingView(symbol);}
}
function openStock(symbol){
  if(!validSymbol(symbol))return;state.stock=symbol;state.chartPeriod='3M';const comp=meta(symbol),p=quotes()[symbol];
  $('stockDetail').innerHTML=`<div class="stock-head"><span class="ticker-avatar">${escapeHTML(symbol.slice(0,2))}</span><div><h2>${escapeHTML(symbol)}</h2><p>${escapeHTML(comp.name)} · ${escapeHTML(comp.sector)}</p></div><div class="stock-head-side"><strong id="detailPrice">${p?fmtMoney(p.close):'—'}</strong><span class="${direction(p?.change_pct)}">${fmtPercent(p?.change_pct)}</span></div></div>
    <div class="detail-buttons"><button id="detailAddWatch" type="button">${state.watchlist.some(c=>c.symbol===symbol)?'✓ Following':'＋ Follow stock'}</button><button id="detailAddHolding" type="button">＋ Portfolio holding</button><button id="detailResearch" type="button">⌕ Research</button><a href="${tickerUrl(symbol)}" target="_blank" rel="noopener">NSE ↗</a></div>
    <div class="detail-chart-shell"><div class="chart-toolbar"><strong>Price history</strong><div class="chart-periods" role="group" aria-label="Chart period">${['1D','1M','3M','6M','1Y'].map(v=>`<button class="${v==='3M'?'selected':''}" data-chart="${v}" type="button">${v}</button>`).join('')}</div></div><div id="stockChartStage" class="chart-stage"></div><div id="chartSourceNote" class="chart-note"></div></div>
    <div class="detail-filings"><h3>Recent company filings</h3><div id="stockFilings"></div></div><div class="detail-extras"><button class="plain-link" type="button" id="nseQuoteBtn">Request NSE quote record ↗</button><div id="nseQuoteOutput" class="subtle"></div></div>`;
  const fil=state.filings.filter(f=>f.symbol===symbol).slice(0,3);
  $('stockFilings').innerHTML=fil.length?fil.map(f=>`<div class="detail-filing"><b>${escapeHTML(categoryLabels[f.category]||f.category)}</b><span>${escapeHTML(f.title)}</span>${f.source_url&&!f.demo?`<a href="${escapeHTML(f.source_url)}" target="_blank" rel="noopener">Original filing ↗</a>`:''}</div>`).join(''):'<div class="empty-simple">No verified filings returned for this company in the selected window.</div>';
  $('detailAddWatch').onclick=()=>{if(!state.watchlist.some(c=>c.symbol===symbol)){state.watchlist.unshift(meta(symbol));persist();renderWatchlist();renderOverview();$('detailAddWatch').textContent='✓ Following';toast(symbol+' added to watchlist')}};
  $('detailAddHolding').onclick=()=>{overlay('stockOverlay',false);openHolding(symbol)};
  $('detailResearch').onclick=()=>{overlay('stockOverlay',false);$('researchSymbol').value=symbol;setPage('research');loadResearchDocuments()};
  $('nseQuoteBtn').onclick=async()=>{
    const el=$('nseQuoteOutput');el.textContent='Requesting NSE website response…';
    try{const data=await api('/api/nse/quote?symbol='+encodeURIComponent(symbol));const raw=data.data||{};el.innerHTML=`<div style="color:#197553;font-weight:780">NSE source response obtained</div><a href="${escapeHTML(data.source_url)}" target="_blank" rel="noopener">Verify on NSE ↗</a><details><summary>Inspect source fields</summary><pre>${escapeHTML(JSON.stringify(raw,null,2).slice(0,5000))}</pre></details>`;}
    catch(err){el.innerHTML=`NSE request unavailable here. <a href="${tickerUrl(symbol)}" target="_blank" rel="noopener">Open official NSE site ↗</a>`;}
  };
  qsa('[data-chart]').forEach(btn=>btn.onclick=()=>{state.chartPeriod=btn.dataset.chart;qsa('[data-chart]').forEach(x=>x.classList.toggle('selected',x===btn));loadStockChart(symbol)});
  overlay('stockOverlay',true);loadStockChart(symbol);
}
function openHolding(symbol=''){
  state.editing=state.holdings.find(x=>x.symbol===symbol)?.symbol||null;
  const old=state.holdings.find(x=>x.symbol===symbol);
  $('editTitle').textContent=old?'EDIT YOUR POSITION':'ADD A POSITION';
  $('holdingTicker').value=symbol||'';$('holdingTicker').readOnly=!!old;
  $('holdingQty').value=old?.quantity||'';
  $('holdingAvg').value=old?.average||'';
  $('removeHoldingBtn').hidden=!old;overlay('editOverlay',true);$('holdingTicker').focus();
}
function submitHolding(event){
  event.preventDefault();const symbol=$('holdingTicker').value.trim().toUpperCase(),quantity=+$('holdingQty').value,average=+$('holdingAvg').value;
  if(!validSymbol(symbol)||!Number.isFinite(quantity)||quantity<=0||!Number.isFinite(average)||average<=0){toast('Enter a ticker, number of shares and average buy price.');return;}
  state.holdings=state.holdings.filter(x=>x.symbol!==symbol);state.holdings.push({symbol,quantity,average});
  if(!state.companies.some(x=>x.symbol===symbol))state.companies.push({symbol,name:symbol,sector:'Unclassified'});
  state.customized=true;persist();overlay('editOverlay',false);renderPortfolio();renderOverview();toast(symbol+' holding saved');refreshData({quiet:true});
}
function addWatch(event){
  event.preventDefault();const symbol=$('addStockTicker').value.trim().toUpperCase(),name=$('addStockName').value.trim();
  if(!validSymbol(symbol)){toast('Enter a valid NSE ticker');return;}
  if(state.watchlist.some(x=>x.symbol===symbol)){toast(symbol+' is already followed');return;}
  if(companySymbols().length>=30){toast('This prototype follows at most 30 NSE tickers at once. Remove one first.');return;}
  const known=meta(symbol);const entry={symbol,name:name||known.name||symbol,sector:known.sector||'Unclassified'};
  state.watchlist.unshift(entry);if(!state.companies.some(x=>x.symbol===symbol))state.companies.push(entry);
  persist();overlay('addOverlay',false);$('addStockForm').reset();renderWatchlist();renderOverview();toast(symbol+' added. Fetching data if available.');refreshData({quiet:true});
}
async function loadResearchDocuments(){
  const symbol=$('researchSymbol').value.trim().toUpperCase();if(!validSymbol(symbol)){toast('Enter a valid NSE ticker');return;}
  $('sourceDocs').innerHTML='<div class="loading-simple">Loading indexed PDFs…</div>';
  try{const data=await api('/api/research/documents?ticker='+encodeURIComponent(symbol));
    const docs=data.documents||[];$('sourceCount').textContent=docs.length;
    $('sourceDocs').innerHTML=docs.length?docs.map(d=>`<div class="source-item"><a href="/api/research/documents/${encodeURIComponent(d.id)}/file" target="_blank" rel="noopener">${escapeHTML(d.name)} ↗</a><small>${escapeHTML(d.kind.replaceAll('_',' '))} · ${d.pages} pages</small></div>`).join(''):
      '<div class="empty-simple">No documents indexed for this ticker. Upload primary-source PDFs to begin.</div>';
  }catch(err){$('sourceDocs').innerHTML=`<div class="error-card">${escapeHTML(err.message)}</div>`;}
}
async function askResearch(){
  const symbol=$('researchSymbol').value.trim().toUpperCase(),question=$('researchQuestion').value.trim();
  if(!validSymbol(symbol)||question.length<8){toast('Enter a valid ticker and a specific question.');return;}
  $('askResearch').disabled=true;$('researchResult').innerHTML='<div class="skeleton-line"></div><div class="skeleton-line"></div>';
  try{const result=await api('/api/research/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticker:symbol,question})});
    const sources=(result.evidence||[]).map((row,i)=>`<details class="evidence-box"><summary><strong>${i+1}. ${escapeHTML(row.document_name)} · page ${row.page}</strong><span>Read excerpt ▾</span></summary><p>${escapeHTML(row.excerpt)}</p><a href="/api/research/documents/${encodeURIComponent(row.document_id)}/file#page=${row.page}" target="_blank" rel="noopener">Open cited PDF ↗</a></details>`).join('');
    $('researchResult').innerHTML=`<div class="answer-header">${result.mode==='llm_grounded'?'Source-grounded AI synthesis':'Primary-source excerpt retrieval'} · ${escapeHTML(symbol)}${symbol==='DEMOCO'?' · FICTIONAL EXAMPLE':''}</div><div class="answer-text">${escapeHTML(result.answer)}</div>${sources}`;
  }catch(err){$('researchResult').innerHTML=`<div class="error-card">${escapeHTML(err.message)}</div>`;}
  finally{$('askResearch').disabled=false;}
}
async function discoverSources(){
  const symbol=$('researchSymbol').value.trim().toUpperCase();if(!validSymbol(symbol)){toast('Enter a ticker first');return;}
  $('sourceDiscovery').innerHTML='<div class="loading-simple">Looking for public source links…</div>';
  try{const r=await api('/api/research/discover?ticker='+encodeURIComponent(symbol));const links=(r.links||[]).slice(0,6).map((x,i)=>`<div class="source-item"><a href="${escapeHTML(x.url)}" target="_blank" rel="noopener">${escapeHTML(x.title||'Company source')} ↗</a><div><button type="button" class="source-import" data-import-index="${i}">Import source PDF</button></div></div>`).join('');
    state.discovered=(r.links||[]).slice(0,6);$('sourceDiscovery').innerHTML=`<div class="subtle">${escapeHTML(r.note||'')}${r.page?` <a target="_blank" rel="noopener" href="${escapeHTML(r.page)}">Screener ↗</a>`:''}</div>${links}`;
    qsa('[data-import-index]').forEach(b=>b.onclick=()=>{const found=state.discovered[+b.dataset.importIndex];if(found)importPdfUrl(found.url,found.kind,found.title||'Company source.pdf')});}
  catch(err){$('sourceDiscovery').innerHTML=`<div class="error-card">${escapeHTML(err.message)}</div>`;}
}
async function importPdfUrl(url,kind='annual_report',name='Primary source.pdf'){
  const symbol=$('researchSymbol').value.trim().toUpperCase();if(!validSymbol(symbol)){toast('Enter a valid ticker');return;}
  if(!url.startsWith('https://')){toast('Use a direct public HTTPS PDF URL');return;}
  toast('Importing source document if the provider allows access…');
  try{await api('/api/research/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticker:symbol,url,kind,name})});await loadResearchDocuments();toast('Source PDF indexed successfully.');}
  catch(err){toast(err.message);}
}
async function uploadResearchPDF(file){
  if(!file)return;if(file.size>20*1024*1024){toast('Maximum PDF size: 20 MB');return;}
  const symbol=$('researchSymbol').value.trim().toUpperCase();if(!validSymbol(symbol)){toast('Enter valid ticker');return;}
  toast('Indexing the uploaded PDF…');
  try{const p=new URLSearchParams({ticker:symbol,name:file.name,kind:$('sourceKind').value});await api('/api/research/upload?'+p,{method:'POST',headers:{'Content-Type':'application/pdf'},body:file});await loadResearchDocuments();toast('Document indexed. Ask a question to see source citations.');}
  catch(err){toast(err.message);}
  finally{$('sourceUpload').value='';}
}
function register(){
  qsa('[data-nav]').forEach(btn=>btn.addEventListener('click',event=>{event.preventDefault();setPage(btn.dataset.nav)}));
  $('refreshBtn').onclick=()=>refreshData({force:true});
  $('dataInfoBtn').onclick=()=>overlay('infoOverlay');$('statusDetails').onclick=()=>overlay('infoOverlay');
  $('closeInfo').onclick=()=>overlay('infoOverlay',false);$('closeStock').onclick=()=>overlay('stockOverlay',false);
  $('closeEdit').onclick=()=>overlay('editOverlay',false);$('closeAdd').onclick=()=>overlay('addOverlay',false);
  qsa('.overlay').forEach(el=>el.onclick=e=>{if(e.target===el)overlay(el.id,false)});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')qsa('.overlay.open').forEach(x=>overlay(x.id,false))});
  $('stockSearch').oninput=renderWatchlist;$('signalSearch').oninput=renderSignals;$('showRoutine').onchange=renderSignals;
  $('addStockBtn').onclick=()=>overlay('addOverlay');$('addStockForm').onsubmit=addWatch;
  $('addHoldingBtn').onclick=()=>openHolding();$('holdingForm').onsubmit=submitHolding;
  $('removeHoldingBtn').onclick=()=>{if(!state.editing)return;const symbol=state.editing;state.holdings=state.holdings.filter(x=>x.symbol!==symbol);state.customized=true;state.editing=null;persist();overlay('editOverlay',false);renderPortfolio();renderOverview();toast(symbol+' removed')};
  $('clearHoldingsBtn').onclick=()=>{if(!confirm('Remove all holdings saved on this device?'))return;state.holdings=[];state.customized=true;persist();renderPortfolio();renderOverview()};
  $('resetHoldingsBtn').onclick=()=>{state.holdings=starterHoldings.map(x=>({...x}));state.customized=false;persist();renderPortfolio();renderOverview();refreshData({quiet:true})};
  $('digestPeriods').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.hours=+b.dataset.hours;persist();renderSignals();refreshData({quiet:true})});
  $('moveRule').oninput=e=>{$('moveRuleValue').textContent='±'+Number(e.target.value).toFixed(1)+'%'};
  $('volumeRule').oninput=e=>{$('volumeRuleValue').textContent=Number(e.target.value).toFixed(1)+'×'};
  const updateRule=()=>{state.priceRule=+$('moveRule').value;state.volumeRule=+$('volumeRule').value;persist();refreshData({quiet:true})};
  $('moveRule').onchange=updateRule;$('volumeRule').onchange=updateRule;
  $('loadSourcesBtn').onclick=loadResearchDocuments;$('askResearch').onclick=askResearch;
  $('findSourceLinks').onclick=discoverSources;$('importPdfUrl').onclick=()=>importPdfUrl($('pdfUrl').value.trim(),$('sourceKind').value,'Imported primary source.pdf');$('sourceUpload').onchange=e=>uploadResearchPDF(e.target.files[0]);
  qsa('[data-q]').forEach(btn=>btn.onclick=()=>{$('researchQuestion').value=btn.dataset.q;$('researchQuestion').focus()});
  $('loadExample').onclick=()=>{$('researchSymbol').value='DEMOCO';loadResearchDocuments();toast('DEMOCO is a fictional, source-cited practice case.')};
  $('openPreview').onclick=()=>location.assign(`${location.pathname}?preview=1#overview`);
}
async function init(){
  register();
  try{const data=await api('/api/portfolio');state.companies=data.companies||[];state.watchlist=Array.isArray(state.storedWatchlist)?state.storedWatchlist:state.companies.map(x=>({...x}));}
  catch(err){$('statusText').textContent='Backend unavailable: '+err.message;toast(err.message);return;}
  const page=location.hash.replace('#','');if(page && ['overview','watchlist','portfolio','signals','research'].includes(page))setPage(page);
  renderAll();await refreshData();
  window.setInterval(()=>{if(document.visibilityState==='visible'&&!state.activeRequest)refreshData({quiet:true})},4*60*1000);
  window.addEventListener('focus',()=>{if(state.updatedAt&&Date.now()-state.updatedAt.getTime()>4*60*1000)refreshData({quiet:true})});
}
document.addEventListener('DOMContentLoaded',init);
