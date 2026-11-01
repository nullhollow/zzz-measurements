/* Measurement workspaces use canonical records and the shared roster filters. */
const MEASUREMENT_VIEWS=['relationships','rangeFinder','ratioLab','cupProfiles','figurePatterns'];
const RATIO_PRESETS=[['bust','waist'],['hip','waist'],['thigh','hip'],['waist','height']];
const MEASUREMENT_COLOURS={height:'var(--tan)',bust:'var(--bust)',underbust:'var(--brass)',waist:'var(--waist)',hip:'var(--hips)',thigh:'var(--thighs)'};
function measurementDefaults(){
  return {analysisView:'relationships',analysisX:'hip',analysisY:'thigh',analysisBasis:'raw',analysisTrend:true,
    analysisRatio:'hip:waist',analysisCup:'all',analysisBand:'all',analysisPick:''};
}
function readMeasurementHash(raw,out,system){
  if(MEASUREMENT_VIEWS.includes(raw.analysisView))out.analysisView=raw.analysisView;
  for(const key of ['analysisX','analysisY'])if(METRIC_KEYS.includes(raw[key]))out[key]=raw[key];
  if(['raw','height'].includes(raw.analysisBasis))out.analysisBasis=raw.analysisBasis;
  if(typeof raw.analysisTrend==='boolean')out.analysisTrend=raw.analysisTrend;
  if(RATIO_PRESETS.some(p=>p.join(':')===raw.analysisRatio))out.analysisRatio=raw.analysisRatio;
  const sizes=DATA.map(d=>Analysis.sizeParts(d[system])).filter(Boolean);
  if(raw.analysisCup==='all'||sizes.some(s=>s.cup===raw.analysisCup))out.analysisCup=raw.analysisCup;
  if(raw.analysisBand==='all'||typeof raw.analysisBand==='string'&&sizes.some(s=>(!out.analysisCup||out.analysisCup==='all'||s.cup===out.analysisCup)&&String(s.band)===raw.analysisBand))out.analysisBand=raw.analysisBand;
  if(bySlug.has(raw.analysisPick))out.analysisPick=raw.analysisPick;
}
function measurementHTML(list){
  const mode=state.analysisView;
  return `<div class="toolform analysis-switch"><label for="analysisView">${esc(t('analysisViewLabel'))}<select id="analysisView">${MEASUREMENT_VIEWS.map(k=>`<option value="${k}"${mode===k?' selected':''}>${esc(t(k))}</option>`).join('')}</select></label><button class="btn" id="shareAnalysis">${esc(t('analysisShare'))}</button></div>`+
    (mode==='relationships'?relationshipHTML(list):mode==='rangeFinder'?rangeFinderHTML():mode==='ratioLab'?ratioLabHTML(list):mode==='cupProfiles'?cupProfilesHTML(list):figurePatternsHTML(list));
}
function analysisNumber(value,suffix='',decimals=1){return value==null?'—':fmt(value,decimals)+suffix;}
function analysisTable(records,columns,expanded=false){
  const table=`<div class="analysis-tablewrap"><table class="tooltable analysis-table"><thead><tr><th scope="col">${esc(t('name'))}</th>${columns.map(c=>`<th scope="col">${esc(c.label)}</th>`).join('')}<th scope="col"><span class="sr">${esc(t('compare'))}</span></th></tr></thead><tbody>${records.map(d=>`<tr${d.slug===state.analysisPick?' class="analysis-current"':''}><td><a href="${esc(charHref(d))}" data-tool-profile="${esc(d.slug)}">${esc(nameOf(d))}</a></td>${columns.map(c=>`<td>${esc(c.text(d))}</td>`).join('')}<td>${analysisCompareButton(d)}</td></tr>`).join('')||`<tr><td colspan="${columns.length+2}">${esc(t('noValues'))}</td></tr>`}</tbody></table></div>`;
  return expanded?table:`<details class="tooldata"><summary>${esc(t('dataTable'))} · ${records.length}</summary>${table}</details>`;
}
function analysisCompareButton(d){
  return `<button class="btn" data-analysis-add="${esc(d.slug)}" aria-pressed="${state.compare.includes(d.slug)}" aria-label="${esc((state.compare.includes(d.slug)?t('removeFromCompare'):t('addCompare'))+': '+nameOf(d))}">${esc(t(state.compare.includes(d.slug)?'added':'cmpShort'))}</button>`;
}
function analysisInspection(list){
  const d=list.find(d=>d.slug===state.analysisPick);if(!d)return '';
  return `<section class="analysis-inspect" id="analysisInspection" aria-label="${esc(nameOf(d))}"><img src="character_images/${esc(d.official.replace(/\.png$/,'.webp'))}" alt="" width="75" height="112"><div><a href="${esc(charHref(d))}" data-tool-profile="${esc(d.slug)}" class="analysis-name">${esc(nameOf(d))}</a><dl>${METRIC_KEYS.map(k=>`<div><dt>${esc(t(k))}</dt><dd>${esc(valueText(d,k,'raw'))}</dd></div>`).join('')}</dl></div>${analysisCompareButton(d)}</section>`;
}
function analysisStat(label,value){return `<span>${esc(label)}<strong>${esc(value)}</strong></span>`;}
function relationshipHTML(list){
  const x=state.analysisX,y=state.analysisY,b=state.analysisBasis;
  const points=list.map(d=>({d,x:shownValue(d,x,b),y:shownValue(d,y,b)})).filter(p=>p.x!=null&&p.y!=null);
  const summary=Analysis.relationship(points.map(p=>[p.x,p.y]));
  return `<div class="toolform"><label for="analysisX">${esc(t('analysisXAxis'))}<select id="analysisX">${metricOptions(x)}</select></label><label for="analysisY">${esc(t('analysisYAxis'))}<select id="analysisY">${metricOptions(y)}</select></label><label for="analysisBasis">${esc(t('basis'))}<select id="analysisBasis">${basisOptions(b)}</select></label><label class="analysis-check"><input type="checkbox" id="analysisTrend"${state.analysisTrend?' checked':''}>${esc(t('analysisTrendLabel'))}</label></div><div class="toolstats">${analysisStat(t('analysisPairs'),summary.count)}${analysisStat(t('analysisCorrelation'),analysisNumber(summary.r,'',3))}</div><p class="toolnote">${esc(t('analysisRelationshipNote'))}</p>${points.length?relationshipChart(points,summary):`<p>${esc(t('noValues'))}</p>`}${analysisInspection(list)}${analysisTable(points.map(p=>p.d),[{label:t(x)+' ('+valueSuffix(x,b)+')',text:d=>valueText(d,x,b)},{label:t(y)+' ('+valueSuffix(y,b)+')',text:d=>valueText(d,y,b)}])}`;
}
function relationshipChart(points,summary){
  const w=innerWidth<=700?500:1000,h=440,l=70,r=w-28,top=20,bottom=365;
  const extent=key=>{const v=points.map(p=>p[key]),lo=Math.min(...v),hi=Math.max(...v),pad=(hi-lo||Math.abs(lo)*.1||1)*.07;return [lo-pad,hi+pad];};
  const [xmin,xmax]=extent('x'),[ymin,ymax]=extent('y');
  const sx=v=>l+(v-xmin)/(xmax-xmin)*(r-l),sy=v=>bottom-(v-ymin)/(ymax-ymin)*(bottom-top);
  const ticks=Array.from({length:5},(_,i)=>i/4);
  const axis=ticks.map(p=>{const x=xmin+(xmax-xmin)*p,y=ymin+(ymax-ymin)*p;return `<line class="gridline" x1="${sx(x)}" x2="${sx(x)}" y1="${top}" y2="${bottom}"/><line class="gridline" x1="${l}" x2="${r}" y1="${sy(y)}" y2="${sy(y)}"/><text x="${sx(x)}" y="${bottom+25}" text-anchor="middle">${esc(fmt(x))}</text><text x="${l-10}" y="${sy(y)+5}" text-anchor="end">${esc(fmt(y))}</text>`;}).join('');
  const trend=state.analysisTrend&&summary.slope!=null?`<line class="analysis-trend" x1="${l}" x2="${r}" y1="${sy(summary.intercept+summary.slope*xmin)}" y2="${sy(summary.intercept+summary.slope*xmax)}"/>`:'';
  return `<div class="analysis-chart"><svg viewBox="0 0 ${w} ${h}" class="analysis-scatter" role="group" aria-label="${esc(t('relationships'))}"><defs><clipPath id="analysisPlotClip"><rect x="${l}" y="${top}" width="${r-l}" height="${bottom-top}"/></clipPath></defs>${axis}<g clip-path="url(#analysisPlotClip)">${trend}${[...points].sort((a,b)=>Number(state.compare.includes(a.d.slug)||a.d.slug===state.analysisPick)-Number(state.compare.includes(b.d.slug)||b.d.slug===state.analysisPick)).map(p=>`<g class="analysis-point${p.d.slug===state.analysisPick?' picked':''}${state.compare.includes(p.d.slug)?' compared':''}" data-analysis-pick="${esc(p.d.slug)}" tabindex="0" role="button" aria-label="${esc(nameOf(p.d)+': '+valueText(p.d,state.analysisX,state.analysisBasis)+' / '+valueText(p.d,state.analysisY,state.analysisBasis))}"><title>${esc(nameOf(p.d)+': '+fmt(p.x)+' / '+fmt(p.y))}</title><circle class="point-hit" cx="${sx(p.x)}" cy="${sy(p.y)}" r="13"/><circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="5"/></g>`).join('')}</g><text x="${(l+r)/2}" y="425" text-anchor="middle">${esc(t(state.analysisX)+' ('+valueSuffix(state.analysisX,state.analysisBasis).trim()+')')}</text><text transform="translate(18 ${(top+bottom)/2}) rotate(-90)" text-anchor="middle">${esc(t(state.analysisY)+' ('+valueSuffix(state.analysisY,state.analysisBasis).trim()+')')}</text></svg></div>`;
}
function activeAnalysisRanges(){return Object.fromEntries(Object.entries(state.rng).filter(([k])=>!rangeFull(k)));}
function rangeControlsHTML(){
  return `<div class="analysis-ranges">${RANGES.map(m=>{const [lo,hi]=dispBounds(m.k),values=state.rng[m.k]||BOUNDS[m.k];return `<fieldset data-analysis-range="${m.k}"><legend style="color:${MEASUREMENT_COLOURS[m.lk]}">${esc(t(m.lk))} <span>(${esc(USUF().trim())})</span></legend><div class="analysis-range-numbers"><label>${esc(t('analysisMinimum'))}<input class="toolinput" data-range-number="lo" type="number" step="any" min="${lo}" max="${hi}" value="${Number(toDisp(values[0]).toFixed(3))}"></label><span>–</span><label>${esc(t('analysisMaximum'))}<input class="toolinput" data-range-number="hi" type="number" step="any" min="${lo}" max="${hi}" value="${Number(toDisp(values[1]).toFixed(3))}"></label><button class="lnk" type="button" data-analysis-reset="${m.k}" aria-label="${esc(t('resetRanges')+': '+t(m.lk))}">↺</button></div><div class="dual"><div class="dtr"><i></i></div><input data-range-slider="lo" type="range" min="${lo}" max="${hi}" step="0.1" value="${toDisp(values[0])}" aria-label="${esc(t(m.lk)+' '+t('analysisMinimum'))}"><input data-range-slider="hi" type="range" min="${lo}" max="${hi}" step="0.1" value="${toDisp(values[1])}" aria-label="${esc(t(m.lk)+' '+t('analysisMaximum'))}"></div></fieldset>`;}).join('')}</div><button class="btn" id="analysisResetRanges">${esc(t('resetRanges'))}</button>`;
}
function rangeFinderHTML(){
  return `${rangeControlsHTML()}<div id="analysisRangeResults" aria-live="polite">${rangeResultsHTML()}</div>`;
}
function rangeResultsHTML(){
  const ranges=activeAnalysisRanges(),base=filtered(true),ranked=base.map(d=>({d,failures:Analysis.rangeFailures(d,ranges)}));
  const exact=ranked.filter(r=>!r.failures.length).map(r=>r.d),near=ranked.filter(r=>r.failures.length).sort((a,b)=>a.failures.length-b.failures.length||gap(a)-gap(b)).slice(0,8);
  function gap(r){return r.failures.reduce((s,f)=>s+(f.value==null?1:Math.abs(f.value-f.limit)/(BOUNDS[f.field][1]-BOUNDS[f.field][0]||1)),0);}
  const columns=METRIC_KEYS.map(k=>({label:t(k),text:d=>valueText(d,k,'raw')}));
  return `<div class="selectionhead"><h3>${esc(t('analysisExactMatches'))} · ${exact.length}</h3></div>${analysisTable(exact,columns,true)}${near.length?`<details class="tooldata" open><summary>${esc(t('analysisNearMatches'))} · ${near.length}</summary>${analysisTable(near.map(r=>r.d),[{label:t('analysisOutsideRange'),text:d=>near.find(r=>r.d===d).failures.map(f=>{const m=RANGES.find(m=>m.k===f.field);return t(m.lk)+': '+(f.value==null?t('analysisMissing'):fmt(toDisp(f.value))+USUF()+' ('+(f.value<f.limit?'↑':'↓')+fmt(toDisp(Math.abs(f.value-f.limit)))+USUF()+')');}).join(' · ')}],true)}</details>`:''}`;
}
function ratioLabHTML(list){
  const [a,b]=state.analysisRatio.split(':'),ratio=d=>Analysis.ratio(d,a,b);
  const records=list.filter(d=>ratio(d)!=null).sort((x,y)=>ratio(y)-ratio(x)),summary=Analysis.numericSummary(records.map(ratio));
  return `<div class="toolform"><label for="analysisRatio">${esc(t('ratioLab'))}<select id="analysisRatio">${RATIO_PRESETS.map(([x,y])=>`<option value="${x}:${y}"${state.analysisRatio===x+':'+y?' selected':''}>${esc(t(x)+' ÷ '+t(y))}</option>`).join('')}</select></label></div><div class="analysis-formula">${esc(t(a))}<span>÷</span>${esc(t(b))}</div><div class="toolstats">${analysisStat(t('population'),summary.count)}${analysisStat(t('median'),analysisNumber(summary.median,'',3))}${analysisStat(t('analysisMiddle50'),summary.count?analysisNumber(summary.q1,'',3)+'–'+analysisNumber(summary.q3,'',3):'—')}</div>${ratioHistogram(records,ratio)}${analysisTable(records,[{label:t('analysisRatioValue'),text:d=>fmt(ratio(d),3)},{label:t(a),text:d=>valueText(d,a,'raw')},{label:t(b),text:d=>valueText(d,b,'raw')}],true)}`;
}
function ratioHistogram(records,ratio){
  const dist=Analysis.distribution(records.map(ratio));if(!dist.count)return `<p>${esc(t('noValues'))}</p>`;
  const w=innerWidth<=700?500:1000,left=50,right=w-30,base=180,lo=dist.bins[0].lo,hi=dist.bins.at(-1).hi;
  const sx=v=>lo===hi?(left+right)/2:left+(v-lo)/(hi-lo)*(right-left),peak=Math.max(...dist.bins.map(b=>b.count));
  return `<div class="analysis-chart"><svg class="analysis-ratio-chart" viewBox="0 0 ${w} 245" role="img" aria-label="${esc(t('ratioLab'))}">${dist.bins.map(b=>{const bw=lo===hi?80:(right-left)/dist.bins.length-4,x=lo===hi?sx(lo)-40:sx(b.lo),h=b.count/peak*140;return `<rect class="ratio-bar" x="${x}" y="${base-h}" width="${bw}" height="${h}"/><text x="${x+bw/2}" y="${base-h-8}" text-anchor="middle">${b.count}</text>`;}).join('')}<line class="analysis-median" x1="${sx(dist.median)}" x2="${sx(dist.median)}" y1="15" y2="190"/>${[...new Set([lo,hi])].map(v=>`<text x="${sx(v)}" y="215" text-anchor="middle">${fmt(v,3)}</text>`).join('')}</svg></div>`;
}
function cupProfilesHTML(list){
  const system=state.cupSystem,parts=d=>Analysis.sizeParts(d[system]),cups=Analysis.cupDistribution(DATA,system).bins.map(b=>b.cup);
  const bands=[...new Set(DATA.map(parts).filter(p=>p&&(state.analysisCup==='all'||p.cup===state.analysisCup)).map(p=>p.band))].sort((a,b)=>a-b);
  const records=list.filter(d=>{const p=parts(d);return p&&(state.analysisCup==='all'||p.cup===state.analysisCup)&&(state.analysisBand==='all'||p.band===+state.analysisBand);});
  const stats=METRIC_KEYS.map(k=>({key:k,...Analysis.numericSummary(records.map(d=>Analysis.value(d,k)))}));
  return `<div class="toolform"><label for="analysisSystem">${esc(t('cupSystem'))}<select id="analysisSystem">${['uk','us','eu'].map(s=>`<option value="${s}"${s===system?' selected':''}>${s.toUpperCase()}</option>`).join('')}</select></label><label for="analysisCup">${esc(t('cupLetters'))}<select id="analysisCup"><option value="all">${esc(t('analysisAllCups'))}</option>${cups.map(c=>`<option value="${c}"${state.analysisCup===c?' selected':''}>${c}</option>`).join('')}</select></label><label for="analysisBand">${esc(t('sourceBand'))}<select id="analysisBand"><option value="all">${esc(t('analysisAllBands'))}</option>${bands.map(b=>`<option value="${b}"${state.analysisBand===String(b)?' selected':''}>${b}</option>`).join('')}</select></label></div><p class="toolnote">${esc(t('analysisCupNote'))}</p><div class="toolstats">${analysisStat(t('analysisGroupCount'),records.length)}</div>${records.some(d=>d[system].startsWith('≈'))?`<p class="toolnote">${esc(t('estimatedSizesNote'))}</p>`:''}<div class="analysis-tablewrap"><table class="tooltable analysis-cup-stats"><thead><tr><th>${esc(t('metric'))}</th><th>${esc(t('median'))}</th><th>${esc(t('analysisMiddle50'))}</th><th>${esc(t('population'))}</th></tr></thead><tbody>${stats.map(s=>`<tr><th scope="row" style="color:${MEASUREMENT_COLOURS[s.key]}">${esc(t(s.key))}</th><td>${esc(analysisNumber(s.median==null?null:toDisp(s.median),USUF()))}</td><td>${s.count?`${esc(fmt(toDisp(s.q1)))}–${esc(fmt(toDisp(s.q3))+USUF())}`:'—'}</td><td>${s.count}${records.length?' / '+records.length:''}</td></tr>`).join('')}</tbody></table></div>${analysisTable(records,[{label:cupSizeLabel(),text:d=>cupText(d)},...METRIC_KEYS.map(k=>({label:t(k),text:d=>valueText(d,k,'raw')}))])}`;
}
function figurePatternsHTML(list){
  return `<p class="toolnote">${esc(t('analysisPatternNote'))}</p><div id="analysisPatternResults">${patternResultsHTML(list)}</div><details class="tooldata"><summary>${esc(t('ranges'))}</summary>${rangeControlsHTML()}</details>`;
}
function patternResultsHTML(list){
  return `<div class="analysis-pattern-wrap" tabindex="0" aria-label="${esc(t('figurePatterns'))}">${figurePatternsChart(list)}</div>${analysisInspection(list)}<div class="toolstats">${analysisStat(t('analysisExactMatches'),list.length+' / '+filtered(true).length)}</div>${analysisTable(list,METRIC_KEYS.map(k=>({label:t(k),text:d=>valueText(d,k,'raw')})))}`;
}
function figurePatternsChart(list){
  const keys=['height','bust','underbust','waist','hip','thigh'],w=1000,top=65,bottom=385;
  const xx=i=>65+i*174,yy=p=>bottom-p*(bottom-top),matching=new Set(list.map(d=>d.slug)),ranges=activeAnalysisRanges();
  const all=filtered(true),populations=Object.fromEntries(keys.map(k=>[k,DATA.map(d=>Analysis.value(d,k))]));
  const percentile=(d,k)=>Analysis.percentile(Analysis.value(d,k),populations[k]);
  const lines=[...all].sort((a,b)=>Number(matching.has(a.slug))*2+Number(state.compare.includes(a.slug))-Number(matching.has(b.slug))*2-Number(state.compare.includes(b.slug)));
  return `<svg id="analysisPatterns" viewBox="0 0 ${w} 445" role="group" aria-label="${esc(t('figurePatterns'))}">${[0,.25,.5,.75,1].map(p=>`<line class="gridline" x1="45" x2="950" y1="${yy(p)}" y2="${yy(p)}"/><text x="25" y="${yy(p)+4}" text-anchor="end">${Math.round(p*100)}</text>`).join('')}${lines.map(d=>{let pen=false;const path=keys.map((k,i)=>{const p=percentile(d,k);if(p==null){pen=false;return '';}const segment=(pen?'L':'M')+xx(i)+','+yy(p);pen=true;return segment;}).join('');return `<path d="${path}" class="analysis-pattern-line${matching.has(d.slug)?' matches':''}${state.compare.includes(d.slug)?' compared':''}${state.analysisPick===d.slug?' picked':''}" data-analysis-pick="${esc(d.slug)}" tabindex="0" role="button" aria-label="${esc(nameOf(d))}"><title>${esc(nameOf(d))}</title></path>`;}).join('')}${keys.map((k,i)=>{const field=Analysis.fields[k],range=ranges[field],values=populations[k].filter(v=>v!=null),low=range?Analysis.percentileAt(range[0],values):0,high=range?Analysis.percentileAt(range[1],values):1;return `<g class="analysis-brush" data-brush-key="${k}" data-brush-index="${i}" style="--metric:${MEASUREMENT_COLOURS[k]}"><text x="${xx(i)}" y="30" text-anchor="middle">${esc(t(k))}</text><line class="pattern-axis" x1="${xx(i)}" x2="${xx(i)}" y1="${top}" y2="${bottom}"/><rect class="brush-fill" x="${xx(i)-9}" y="${yy(high)}" width="18" height="${Math.max(2,yy(low)-yy(high))}"${range?'':' visibility="hidden"'}/><rect class="brush-hit" x="${xx(i)-18}" y="${top}" width="36" height="${bottom-top}"/><text x="${xx(i)}" y="422" text-anchor="middle">${esc(fmt(toDisp(Math.min(...values))))}–${esc(fmt(toDisp(Math.max(...values)))+USUF())}</text></g>`;}).join('')}</svg>`;
}
function bindMeasurement(){
  $('#analysisView').onchange=e=>toolUpdate('analysisView',()=>{state.analysisView=e.target.value;});
  $('#shareAnalysis').onclick=()=>share();
  for(const id of ['analysisX','analysisY','analysisBasis','analysisRatio','analysisCup','analysisBand'])if($('#'+id))$('#'+id).onchange=e=>toolUpdate(id,()=>{state[id]=e.target.value;if(id==='analysisCup')state.analysisBand='all';});
  if($('#analysisTrend'))$('#analysisTrend').onchange=e=>toolUpdate('analysisTrend',()=>{state.analysisTrend=e.target.checked;});
  if($('#analysisSystem'))$('#analysisSystem').onchange=e=>toolUpdate('analysisSystem',()=>{state.cupSystem=e.target.value;state.analysisCup='all';state.analysisBand='all';try{localStorage.setItem('zzz-cup-system',state.cupSystem);}catch(_){}syncControls();});
  bindAnalysisSelection();bindAnalysisRanges();bindPatternBrush();
}
function bindAnalysisSelection(){
  $$('[data-analysis-pick]').forEach(el=>{const select=()=>{state.analysisPick=el.dataset.analysisPick;render();};el.onclick=select;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};});
  $$('[data-analysis-add]').forEach(el=>el.onclick=()=>toggleCompare(el.dataset.analysisAdd));
}
function bindAnalysisRanges(){
  $$('[data-analysis-range]').forEach(row=>{
    const key=row.dataset.analysisRange,lo=row.querySelector('[data-range-number="lo"]'),hi=row.querySelector('[data-range-number="hi"]');
    const sl=row.querySelector('[data-range-slider="lo"]'),sh=row.querySelector('[data-range-slider="hi"]');
    const paint=()=>{const a=(+sl.value-sl.min)/(sl.max-sl.min)*100,b=(+sh.value-sh.min)/(sh.max-sh.min)*100,fill=row.querySelector('.dtr i');fill.style.left=a+'%';fill.style.width=(b-a)+'%';};
    const apply=(input,slider=false)=>{
      if(!slider&&(!input.checkValidity()||+lo.value>+hi.value)){input.setCustomValidity(+lo.value>+hi.value?t('analysisRangeOrder'):'');input.reportValidity();return;}
      const [min,max]=dispBounds(key),low=+lo.value,high=+hi.value;
      // Editing one endpoint preserves the other endpoint's raw precision.
      const previous=state.rng[key]||BOUNDS[key];
      state.rng[key]=[low,high].map((v,i)=>v===Number(toDisp(previous[i]).toFixed(3))?previous[i]:i===0&&v<=min?BOUNDS[key][0]:i===1&&v>=max?BOUNDS[key][1]:toCmOf(v));
      sl.value=low;sh.value=high;paint();updateFilterBadge();renderActiveFilters();renderFilterPanel();writeHash(true);
      if($('#analysisRangeResults')){$('#analysisRangeResults').innerHTML=rangeResultsHTML();bindAnalysisSelection();$('#count').innerHTML=`<b>${filtered().length}</b> / ${DATA.length} ${esc(t('entries'))}`;}
      else if($('#analysisPatternResults')){$('#analysisPatternResults').innerHTML=patternResultsHTML(filtered());bindAnalysisSelection();bindPatternBrush();}
    };
    for(const input of [lo,hi]){input.oninput=()=>{lo.setCustomValidity('');hi.setCustomValidity('');if(lo.validity.valid&&hi.validity.valid&&+lo.value<=+hi.value)apply(input);};input.onchange=()=>apply(input);}
    sl.oninput=()=>{lo.value=sl.value;if(+sl.value>+sh.value)hi.value=sh.value=sl.value;apply(sl,true);};
    sh.oninput=()=>{hi.value=sh.value;if(+sh.value<+sl.value)lo.value=sl.value=sh.value;apply(sh,true);};paint();
  });
  $$('[data-analysis-reset]').forEach(el=>el.onclick=()=>{delete state.rng[el.dataset.analysisReset];renderFilterPanel();render();});
  if($('#analysisResetRanges'))$('#analysisResetRanges').onclick=()=>{state.rng={};renderFilterPanel();render();};
}
function bindPatternBrush(){
  const svg=$('#analysisPatterns');if(!svg)return;
  $$('.analysis-brush').forEach(axis=>{
    const hit=axis.querySelector('.brush-hit'),fill=axis.querySelector('.brush-fill'),key=axis.dataset.brushKey,field=Analysis.fields[key];let start=null;
    const y=e=>Math.max(65,Math.min(385,(e.clientY-svg.getBoundingClientRect().top)/svg.getBoundingClientRect().height*445));
    hit.onpointerdown=e=>{if(e.button!==0)return;e.preventDefault();start=y(e);hit.setPointerCapture(e.pointerId);fill.removeAttribute('visibility');fill.setAttribute('y',start);fill.setAttribute('height',2);};
    hit.onpointermove=e=>{if(start==null)return;const end=y(e);fill.setAttribute('y',Math.min(start,end));fill.setAttribute('height',Math.max(2,Math.abs(end-start)));};
    hit.onpointerup=e=>{if(start==null)return;const end=y(e);if(Math.abs(end-start)<4)delete state.rng[field];else state.rng[field]=Analysis.percentileRange(DATA.map(d=>d[field]),1-(Math.max(start,end)-65)/320,1-(Math.min(start,end)-65)/320);start=null;renderFilterPanel();render();};
    hit.onpointercancel=()=>{start=null;render();};
  });
}
