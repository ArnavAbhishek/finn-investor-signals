/* Source-first, small and explainable: FINN v4 extension.
 * Financial figures in the case are dated company-issued filings, NEVER live quotes.
 */
'use strict';
let verifiedCase = null;
let activeLens = 'narrative';
let activeMetric = 'revenue';
let lensToken = 0;
const lensNames = {
  business:'Business snapshot',financial:'Financial snapshot',trajectory:'Performance trajectory',
  balance:'Balance-sheet health',cash:'Cash quality',narrative:'Management story vs numbers',
  guidance:'Management guidance',bullbear:'Bull / bear'
};
function styleCaseFeature(data){
  const q=data.quarters || [];
  if(!q.length)return;
  const revenue=q.at(-1).revenue;
  $('featureRevenue').textContent=`₹${Number(revenue).toLocaleString('en-IN')} Cr`;
  const row=data.headlines.rows.find(x=>x.metric==='revenue');
  $('featureGrowth').textContent=`${row.qoq_pct>=0?'+':''}${row.qoq_pct.toFixed(2)}% QoQ`;
  $('featureBars').innerHTML=q.map(x=>`<i title="${escapeHTML(x.period)} · ₹${Number(x.revenue).toLocaleString('en-IN')} crore" style="height:${Math.round(x.revenue/Math.max(...q.map(p=>p.revenue))*100)}%"></i>`).join('');
}
function sourceLink(cite){
  const url=String(cite?.url||'');
  if(!url.startsWith('https://') && !url.startsWith('/api/'))return '';
  return `<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(cite.title||'Original primary document')}${cite.page?' · p. '+Number(cite.page):''} ↗</a>`;
}
function plotQuarter(metric){
  if(!verifiedCase)return;
  const points=verifiedCase.quarters, max=Math.max(...points.map(x=>Number(x[metric]||0)));
  $('fourQuarterViz').innerHTML=points.map(row=>`<div class="quarter-col"><b>₹${Number(row[metric]).toLocaleString('en-IN')}</b><i style="height:${Math.max(7,Math.round(row[metric]/max*80))}%"></i><span>${escapeHTML(row.period)}</span></div>`).join('');
  const description={revenue:'Consolidated revenue',operating_profit:'Company-reported operating profit (not EBITDA)',pbt:'Profit before tax',pat:'Profit after tax'}[metric];
  $('quarterFoot').innerHTML=`${escapeHTML(description)} · ₹ crore, consolidated IFRS. <a href="${escapeHTML(verifiedCase.sources.find(x=>x.key==='q4').url)}" target="_blank" rel="noopener">Q3–Q4 source ↗</a> · <a href="${escapeHTML(verifiedCase.sources.find(x=>x.key==='q1').url)}" target="_blank" rel="noopener">Q1 source ↗</a> · <a href="${escapeHTML(verifiedCase.sources.find(x=>x.key==='q2').url)}" target="_blank" rel="noopener">Q2 source ↗</a>`;
}
function renderResultsTable(){
  if(!verifiedCase)return;
  const lines=verifiedCase.headlines.rows;
  $('quarterRows').innerHTML=lines.map(x=>`<tr><td>${escapeHTML(x.label)}</td><td class="${x.current==null?'missing-metric':''}">${x.current==null?'Not verified':Number(x.current).toLocaleString('en-IN')}</td><td>${x.qoq_pct==null?'—':fmtPercent(x.qoq_pct)}</td><td>${x.yoy_pct==null?'—':fmtPercent(x.yoy_pct)}</td></tr>`).join('');
  $('resultsOriginal').href=verifiedCase.sources.find(x=>x.key==='q2').url;
}
function showVerifiedDocs(symbol){
  if(symbol==='INFY'&&verifiedCase){
    const sourceKeys=['annual','q4','q1','q2','call'];
    $('verifiedSourceList').innerHTML=`<div class="angle-status">VERIFIED PRIMARY SOURCES</div>`+sourceKeys.map(key=>{
      const row=verifiedCase.sources.find(x=>x.key===key);
      return `<div class="source-item">${sourceLink(row)}<small>${escapeHTML(row.kind.replaceAll('_',' '))} · company-issued</small></div>`;
    }).join('');
  }else $('verifiedSourceList').innerHTML='';
}
async function showLens(lens=activeLens){
  activeLens=lens;
  qsa('[data-angle]').forEach(btn=>btn.classList.toggle('selected',btn.dataset.angle===lens));
  const ticker=$('researchSymbol').value.toUpperCase().trim();
  if(!validSymbol(ticker)){$('angleResult').textContent='Enter a valid NSE ticker.';return;}
  const token=++lensToken;
  $('angleResult').innerHTML='<div class="loading-simple">Reading the evidence…</div>';
  $('caseStatus').textContent=ticker==='INFY'?'Source-verified case':'Primary PDF retrieval';
  $('quarterPanel').hidden=ticker!=='INFY';$('resultsPanel').hidden=ticker!=='INFY';
  showVerifiedDocs(ticker);
  try{
    const data=await api(`/api/research/angles?${new URLSearchParams({ticker,angle:lens})}`);
    if(token!==lensToken)return;
    const answer=data.angles?.[0];
    if(!answer){$('angleResult').textContent='No research lenses returned.';return;}
    if(!answer.findings?.length){
      $('angleResult').innerHTML=`<h3>${escapeHTML(lensNames[lens])}</h3><p>No primary PDF evidence indexed for ${escapeHTML(ticker)}. Use the Source library below to upload an annual report and earnings-call transcript. FINN will not guess missing numbers.</p>`;
      return;
    }
    const extractive = data.status==='primary_pdf_evidence';
    const findings=answer.findings.map(item=>`<article><p>${escapeHTML(item.text)}</p>${sourceLink(item.citation)}</article>`).join('');
    $('angleResult').innerHTML=`<div class="angle-status">${extractive?'RETRIEVED EXCERPTS · NOT ANALYST CONCLUSIONS':'VERIFIED PRIMARY-SOURCE FACTS'}</div><h3>${escapeHTML(answer.title)}</h3><div class="angle-findings">${findings}</div>`;
  }catch(error){if(token!==lensToken)return;$('angleResult').innerHTML=`<div class="error-card">${escapeHTML(error.message)}</div>`;}
}
function activateTicker(ticker){
  $('researchSymbol').value=ticker;
  qsa('.quick-ticker').forEach(x=>x.classList.toggle('active',x.dataset.company===ticker));
  if(state.page!=='research')setPage('research');
  showLens(activeLens);loadResearchDocuments();
}
function enableNotifications(){
  if(!('Notification' in window)){toast('This browser does not support desktop notifications');return;}
  Notification.requestPermission().then(permission=>{
    $('notifyBtn').textContent=permission==='granted'?'Alerts enabled ✓':'Enable browser alerts';
    toast(permission==='granted'?'You will be notified when new priority filings appear while FINN is open.':'Notification permission was not granted.');
  });
}
function notifyPriorityFilings(newFilings){
  if(!('Notification' in window)||Notification.permission!=='granted'||!newFilings?.length)return;
  const selected=newFilings[0];
  try{new Notification(`FINN · ${newFilings.length} priority filing${newFilings.length>1?'s':''}`,{
      body:`${selected.symbol} · ${selected.title}`.slice(0,180),tag:'finn-new-priority',silent:false
    });}catch(_){/* Browsers may block notification API despite permission */}
}
function initV4(){
  $('featureResearchBtn').onclick=()=>activateTicker('INFY');
  $('jumpToInfy').onclick=()=>activateTicker('INFY');
  qsa('[data-angle]').forEach(b=>b.onclick=()=>showLens(b.dataset.angle));
  qsa('[data-metric]').forEach(b=>b.onclick=()=>{
    activeMetric=b.dataset.metric;qsa('[data-metric]').forEach(x=>x.classList.toggle('selected',x===b));plotQuarter(activeMetric);
  });
  qsa('[data-company]').forEach(b=>b.onclick=()=>activateTicker(b.dataset.company));
  $('researchSymbol').addEventListener('change',()=>{showLens(activeLens);loadResearchDocuments()});
  $('loadSourcesBtn').addEventListener('click',()=>showLens(activeLens));
  $('notifyBtn').onclick=enableNotifications;
  $('filingCategory').onchange=()=>renderSignals();
  api('/api/case/INFY').then(data=>{
    verifiedCase=data;styleCaseFeature(data);showVerifiedDocs($('researchSymbol').value.trim().toUpperCase());
    plotQuarter(activeMetric);renderResultsTable();showLens(activeLens);
  }).catch(err=>{$('caseStatus').textContent='Case unavailable';$('angleResult').textContent=err.message;});
}
document.addEventListener('DOMContentLoaded',initV4);
