/* Exploration state is separate from the official roster and its derived rules. */
const TOOL_VIEWS=['distribution','matches','game','sandbox'];
const METRIC_KEYS=['height','bust','underbust','waist','hip','thigh'];
const COMPARE_ROWS=['height','waist','hip','thigh','cup','bust','underbust','sizes','whr','whtr','shape','build','thighNote','figureRead'];
const SANDBOX_SLUG='~sandbox';
let gameRound=null, gameScore={correct:0,total:0,streak:0};
function explorerDefaults(){
  return {compareRows:null,compareBase:'',compareHeight:160,sandbox:null,matchSource:'',matchBasis:'raw',matchWeights:null,
    distMetric:'waist',distBasis:'raw',gameMetric:'waist',gameBasis:'raw'};
}
function validSandbox(raw){
  if(!raw || typeof raw!=='object' || !Number.isFinite(raw.stature_cm) || raw.stature_cm<1 || raw.stature_cm>300) return null;
  const out={stature_cm:Number(raw.stature_cm.toFixed(1)),name:typeof raw.name==='string'?raw.name.trim().slice(0,40):''};
  for(const field of Object.values(CIRCUMFERENCES)){
    const v=raw[field];
    if(v!=null && (!Number.isFinite(v)||v<.1||v>300)) return null;
    out[field]=v==null?null:Number(v.toFixed(1));
  }
  return out;
}
function sandboxRecord(){
  if(!state.sandbox) return null;
  const s=state.sandbox, d={...s,slug:SANDBOX_SLUG,display:s.name||t('temporary'),temporary:true};
  for(const field of ['stature_cm',...Object.values(CIRCUMFERENCES)]) d[field.replace('_cm','_in')]=s[field]==null?null:s[field]/2.54;
  d.whr=s.waist_cm&&s.hip_cm?r3(s.waist_cm/s.hip_cm):null;
  d.whtr=s.waist_cm?r3(s.waist_cm/s.stature_cm):null;
  return d;
}
function comparisonRecord(slug){ return slug===SANDBOX_SLUG?sandboxRecord():bySlug.get(slug); }
function readExplorerHash(params){
  let raw={};
  try{ const text=params.get('x'); if(text && text.length<=5000) raw=JSON.parse(text); }catch(_){}
  if(!raw || typeof raw!=='object') return {};
  const out={};
  out.sandbox=validSandbox(raw.sandbox);
  if(Array.isArray(raw.compareRows)){
    const rows=[...new Set(raw.compareRows.filter(k=>COMPARE_ROWS.includes(k)))];
    if(rows.length) out.compareRows=rows;
  }
  if(typeof raw.compareBase==='string') out.compareBase=raw.compareBase;
  if(Number.isFinite(raw.compareHeight)&&raw.compareHeight>=1&&raw.compareHeight<=300) out.compareHeight=Number(raw.compareHeight.toFixed(1));
  if(bySlug.has(raw.matchSource)||raw.matchSource===SANDBOX_SLUG&&out.sandbox) out.matchSource=raw.matchSource;
  for(const key of ['matchBasis','gameBasis']) if(['raw','height'].includes(raw[key])) out[key]=raw[key];
  if(['raw','height','scaled'].includes(raw.distBasis)) out.distBasis=raw.distBasis;
  for(const key of ['distMetric','gameMetric']) if(METRIC_KEYS.includes(raw[key])) out[key]=raw[key];
  if(raw.matchWeights && typeof raw.matchWeights==='object'){
    out.matchWeights=Object.fromEntries(Object.keys(Analysis.fields).map(k=>[k,Number.isFinite(raw.matchWeights[k])?Math.round(Math.max(0,Math.min(1,raw.matchWeights[k]))*100)/100:0]));
  }
  return out;
}
function writeExplorerHash(params){
  const out={}, defaults=explorerDefaults();
  for(const key of Object.keys(defaults)) if(JSON.stringify(state[key])!==JSON.stringify(defaults[key])) out[key]=state[key];
  if(Object.keys(out).length) params.set('x',JSON.stringify(out));
}
function metricOptions(selected){ return METRIC_KEYS.map(k=>`<option value="${k}"${selected===k?' selected':''}>${esc(t(k))}</option>`).join(''); }
function basisOptions(selected,scaled=false){
  return ['raw','height',...(scaled?['scaled']:[])].map(k=>`<option value="${k}"${selected===k?' selected':''}>${esc(t(k==='raw'?'rawMeasurements':k==='height'?'heightAdjusted':'sameHeight'))}</option>`).join('');
}
function figureOptions(selected){
  const records=[...DATA].sort((a,b)=>nameOf(a).localeCompare(nameOf(b),state.lang));
  if(state.sandbox) records.push(sandboxRecord());
  return records.map(d=>`<option value="${esc(d.slug)}"${d.slug===selected?' selected':''}>${esc(nameOf(d))}${d.temporary?' ('+esc(t('temporary'))+')':''}</option>`).join('');
}
function shownValue(record,key,basis='raw'){
  const v=Analysis.value(record,key,basis,state.compareHeight);
  return v==null?null:(basis==='height'&&key!=='height'?v:toDisp(v));
}
function valueSuffix(key,basis){ return basis==='height'&&key!=='height'?'%':USUF(); }
function valueText(d,key,basis){ const v=shownValue(d,key,basis); return v==null?'—':fmt(v)+valueSuffix(key,basis); }
function targetControl(id){
  return `<label for="${id}">${esc(t('targetHeight'))}<input class="toolinput" id="${id}" type="number" min="1" max="300" step="0.1" value="${state.compareHeight}" required></label>`;
}
function setTarget(input){
  if(!input.checkValidity()){ input.reportValidity(); return false; }
  state.compareHeight=+input.value; return true;
}
function openTool(view,source){
  if(!TOOL_VIEWS.includes(view)) return;
  if($('#overlay').classList.contains('open')) closeModal();
  if(source) state.matchSource=source;
  state.view=view; render();
  $('#toolTitle').focus({preventScroll:true});
  $('#toolsView').scrollIntoView({block:'start',behavior:'instant'});
}
$('#toolSelect').addEventListener('change',e=>{ if(e.target.value) openTool(e.target.value); });
window.addEventListener('resize',debounce(()=>{if(state.view==='distribution')renderTool(filtered());},150));
function renderTool(list){
  const root=$('#toolsView');
  const content=state.view==='distribution'?distributionHTML(list):state.view==='matches'?matchesHTML():state.view==='game'?gameHTML():sandboxHTML();
  root.innerHTML=`<div class="toolhead"><h2 id="toolTitle" tabindex="-1">${esc(t(state.view))}</h2></div>${content}`;
  if(state.view==='distribution') bindDistribution();
  else if(state.view==='matches') bindMatches();
  else if(state.view==='game') bindGame();
  else bindSandbox();
}

/* Comparison rows, reference differences and same-height equivalents. */
function rowLabel(key){ return key==='sizes'?'UK / US / EU':t(key==='whr'?'waistHip':key==='whtr'?'waistHeight':key); }
function openCompare(){
  const active=document.activeElement, focusId=active?.id, focusMode=active?.dataset.compareMode;
  const pickerOpen=$('#rowPicker')?.open||false;
  const list=state.compare.map(comparisonRecord).filter(Boolean);
  if(list.length<2){ toast(t('pickTwo')); return; }
  if(!state.compare.includes(state.compareBase)) state.compareBase='';
  const reference=comparisonRecord(state.compareBase), basis=state.compareMode;
  const rowKeys=(state.compareRows||COMPARE_ROWS).filter(k=>!(basis==='height'&&k==='whtr'&&!state.compareRows));
  const numeric=(d,key)=>METRIC_KEYS.includes(key)?shownValue(d,key,basis):['whr','whtr'].includes(key)?d[key]??null:null;
  function text(d,key){
    if(key==='height') return d.temporary?`${fmt(d.stature_cm)} cm\n${fmt(d.stature_cm/2.54)} in`:`${fmt(d.stature_cm)} cm\n${d.ftin_stature}${d.stature_basis==='head'?` · ${fmt(d.cm,0)} ${t('charted')}`:''}`;
    if(CIRCUMFERENCES[key]){
      if(basis==='raw') return d[CIRCUMFERENCES[key]]==null?'—':`${fmt(d[CIRCUMFERENCES[key]])} cm\n${fmt(d[CIRCUMFERENCES[key]]/2.54)} in`;
      return valueText(d,key,basis);
    }
    if(d.temporary){ if(key==='whr'||key==='whtr') return fmtPct(d[key]); return '—'; }
    if(key==='cup') return `${cupLetter(d)}\nUK ${d.uk}`;
    if(key==='sizes') return `${d.uk} / ${d.us} / ${d.eu}`;
    if(key==='whr'||key==='whtr') return fmtPct(d[key]);
    if(key==='figureRead') return readFor(d)||'—';
    if(key==='thighNote') return tagText(tagsFor(d).thighs);
    return tagText(tagsFor(d)[key==='build'?'balance':key])||'—';
  }
  const best={height:'max',waist:'min',hip:'max',thigh:'max',cup:'max'};
  const body=rowKeys.map(key=>{
    const vals=list.map(d=>key==='cup'?(d.temporary?null:cupScore(d)):numeric(d,key));
    // Raw winners retain the original centimetre rule. Adjusted modes share visible ties.
    const ranked=vals.map((v,i)=>v==null?null:key==='cup'?v:key==='height'||basis==='raw'?Analysis.value(list[i],key,'raw'):Analysis.displayed(v));
    const nums=ranked.filter(v=>v!=null), target=nums.length?(best[key]==='min'?Math.min(...nums):Math.max(...nums)):null;
    const direction=best[key]?` <span class="cmpdir" title="${esc(t(best[key]==='min'?'smallerWins':'largerWins'))}">${best[key]==='min'?'↓':'↑'}</span>`:'';
    return `<tr data-metric="${key}"><th scope="row">${esc(rowLabel(key))}${direction}</th>${list.map((d,i)=>{
      let delta='';
      if(reference && d.slug!==reference.slug && key!=='cup'){
        const decimals=['whr','whtr'].includes(key)?3:1;
        const a=vals[i],b=numeric(reference,key);
        const diff=Analysis.difference(a==null?null:Number(a.toFixed(decimals)),b==null?null:Number(b.toFixed(decimals)));
        const suffix=decimals===3?'':basis==='height'&&key!=='height'?' '+t('pp'):USUF();
        if(diff!=null){ const rounded=Number(diff.toFixed(decimals)); delta=`<small class="cmpdelta">${rounded>0?'+':''}${fmt(rounded,decimals)}${esc(suffix)}</small>`; }
      }
      return `<td class="${best[key]&&ranked[i]!=null&&ranked[i]===target?'win':''}${key==='figureRead'?' cmdesc':''}">${esc(text(d,key))}${delta}</td>`;
    }).join('')}</tr>`;
  }).join('');
  const selected=state.compareRows||COMPARE_ROWS, options=[...selected,...COMPARE_ROWS.filter(k=>!selected.includes(k))];
  const rowPicker=`<details class="rowpicker" id="rowPicker"${pickerOpen?' open':''}><summary>${esc(t('rows'))}</summary><div class="rowoptions">${options.map(key=>{
    const index=selected.indexOf(key);
    return `<div class="rowoption"><label><input type="checkbox" id="row-${key}" data-row="${key}"${index>=0?' checked':''}>${esc(rowLabel(key))}</label><button class="btn" id="up-${key}" data-move="${key}" data-direction="-1"${index<=0?' disabled':''} aria-label="${esc(t('moveUp')+': '+rowLabel(key))}">↑</button><button class="btn" id="down-${key}" data-move="${key}" data-direction="1"${index<0||index===selected.length-1?' disabled':''} aria-label="${esc(t('moveDown')+': '+rowLabel(key))}">↓</button></div>`;
  }).join('')}</div><button class="btn" id="restoreRows">${esc(t('restoreRows'))}</button></details>`;
  $('#modal').innerHTML=`<button class="x" id="closeModal" aria-label="${esc(t('close'))}">✕</button>
    <div class="mhead"><h2 id="mTitle">${esc(t('compareTitle'))}</h2><div class="sub2">${list.length} ${esc(t('picked'))}</div>
      <div class="cmpcontrols"><div class="seg" role="group" aria-label="${esc(t('compareBasis'))}">${['raw','height','scaled'].map(k=>`<button id="basis-${k}" data-compare-mode="${k}" aria-pressed="${basis===k}">${esc(t(k==='raw'?'rawMeasurements':k==='height'?'heightAdjusted':'sameHeight'))}</button>`).join('')}</div>
      ${basis==='scaled'?targetControl('compareTarget'):''}
      <label for="compareReference">${esc(t('reference'))}<select id="compareReference"><option value="">${esc(t('noReference'))}</option>${list.map(d=>`<option value="${esc(d.slug)}"${d.slug===state.compareBase?' selected':''}>${esc(nameOf(d))}</option>`).join('')}</select></label>
      ${basis!=='raw'?`<p class="fnote" id="compareBasisNote">${esc(t(basis==='height'?'heightAdjustedNote':'scaledNote'))}</p>`:''}${rowPicker}</div></div>
    <div class="cmpwrap"><table class="cmptable"${basis!=='raw'?' aria-describedby="compareBasisNote"':''}><thead><tr><th scope="col"></th>${list.map(d=>`<th scope="col">${esc(nameOf(d))}${d.temporary?`<small class="cmpdelta">${esc(t('temporary'))}</small>`:''}${d.slug===state.compareBase?`<small class="cmpdelta">${esc(t('referenceMark'))}</small>`:''}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>`;
  if(!$('#overlay').classList.contains('open')) lastFocus=active;
  mctx={slug:null,src:state.art,skin:false,more:null};
  $('#toast').classList.remove('show'); $('#overlay').classList.add('open'); $('#overlay').setAttribute('aria-hidden','false');
  document.body.classList.add('modal-open'); if('inert' in $('#main')) $('#main').inert=true;
  const focus=focusId?document.getElementById(focusId):null;
  (focus&&$('#modal').contains(focus)&&!focus.disabled?focus:focus?.dataset.move?document.getElementById('row-'+focus.dataset.move):focusMode?$(`#basis-${focusMode}`):$('#closeModal')).focus();
  $('#closeModal').onclick=closeModal;
  const update=()=>{ openCompare(); writeHash(true); };
  $$('#modal [data-compare-mode]').forEach(b=>b.onclick=()=>{state.compareMode=b.dataset.compareMode;update();});
  $('#compareReference').onchange=e=>{state.compareBase=e.target.value;update();};
  if($('#compareTarget')) $('#compareTarget').onchange=e=>{if(setTarget(e.target)) update();};
  $$('#modal [data-row]').forEach(input=>input.onchange=()=>{
    const chosen=[...(state.compareRows||COMPARE_ROWS)];
    if(input.checked) chosen.push(input.dataset.row);
    else {if(chosen.length===1){input.checked=true;toast(t('keepRow'));return;} chosen.splice(chosen.indexOf(input.dataset.row),1);}
    state.compareRows=chosen;update();
  });
  $$('#modal [data-move]').forEach(b=>b.onclick=()=>{
    const chosen=[...(state.compareRows||COMPARE_ROWS)],a=chosen.indexOf(b.dataset.move),z=a+Number(b.dataset.direction);
    if(a<0||z<0||z>=chosen.length)return;
    [chosen[a],chosen[z]]=[chosen[z],chosen[a]];state.compareRows=chosen;update();
  });
  $('#restoreRows').onclick=()=>{state.compareRows=null;update();};
}

/* Filtered roster distribution; references are markers, never observations. */
function distributionHTML(list){
  const key=state.distMetric,basis=key==='height'?'raw':state.distBasis;
  const measured=list.map(d=>({d,v:shownValue(d,key,basis)})).filter(x=>x.v!=null);
  const summary=Analysis.distribution(measured.map(x=>x.v));
  const markers=state.compare.map(comparisonRecord).filter(Boolean).map(d=>({d,v:shownValue(d,key,basis)})).filter(x=>x.v!=null);
  let chart='';
  if(summary.count){
    const all=[...measured,...markers].map(x=>x.v), min=Math.min(...all),max=Math.max(...all),span=max-min||1;
    const width=innerWidth<=700?460:920;
    const x=v=>max===min?width/2:65+(v-min)/span*(width-130),base=290,peak=Math.max(...summary.bins.map(b=>b.count));
    const bars=summary.bins.map(b=>{
      const left=x(b.lo),right=x(b.hi),width=summary.bins.length===1?100:Math.max(1,right-left-3),cx=summary.bins.length===1?left+width/2:(left+right)/2;
      const bx=summary.bins.length===1?left-50:left,h=b.count/peak*205;
      return `<g><title>${esc(fmt(b.lo)+'–'+fmt(b.hi)+valueSuffix(key,basis)+': '+b.count)}</title><rect class="bar" x="${bx}" y="${base-h}" width="${width}" height="${h}"/><text x="${summary.bins.length===1?left:cx}" y="${base-h-8}" text-anchor="middle">${b.count}</text></g>`;
    }).join('');
    chart=`<svg class="histogram" viewBox="0 0 ${width} 355" role="img" aria-labelledby="histTitle histDesc"><title id="histTitle">${esc(t('distribution')+': '+t(key))}</title><desc id="histDesc">${esc(t('population')+': '+summary.count+'. '+t('median')+': '+fmt(summary.median)+valueSuffix(key,basis))}</desc><line class="axis" x1="40" y1="290" x2="${width-35}" y2="290"/>${bars}<line class="median" x1="${x(summary.median)}" x2="${x(summary.median)}" y1="60" y2="300"><title>${esc(t('median'))}</title></line>${markers.map((m,i)=>`<g><line class="marker" x1="${x(m.v)}" x2="${x(m.v)}" y1="${25+i*18}" y2="300"/><text x="${x(m.v)}" y="${19+i*18}" text-anchor="middle">${i+1}</text></g>`).join('')}<text x="${x(min)}" y="325" text-anchor="middle">${esc(fmt(min)+(min===max?valueSuffix(key,basis):''))}</text>${min===max?'':`<text x="${x(max)}" y="325" text-anchor="middle">${esc(fmt(max)+valueSuffix(key,basis))}</text>`}</svg>`;
  }
  return `<div class="toolform"><label for="distMetric">${esc(t('metric'))}<select id="distMetric">${metricOptions(key)}</select></label><label for="distBasis">${esc(t('basis'))}<select id="distBasis"${key==='height'?' disabled':''}>${basisOptions(basis,true)}</select></label>${basis==='scaled'?targetControl('distTarget'):''}</div>
    <p class="toolnote">${esc(t('distributionNote'))}</p>${summary.count?`<div class="toolstats"><span>${esc(t('population'))}<strong>${summary.count}</strong></span><span>${esc(t('median'))}<strong>${esc(fmt(summary.median)+valueSuffix(key,basis))}</strong></span></div>${chart}<div class="markerlist">${markers.map((m,i)=>`<span>${i+1}. ${esc(nameOf(m.d))}: ${esc(fmt(m.v)+valueSuffix(key,basis))}</span>`).join('')}</div>`:`<p>${esc(t('noValues'))}</p>`}
    <details class="tooldata"><summary>${esc(t('dataTable'))}</summary><table class="tooltable"><thead><tr><th>${esc(t('name'))}</th><th>${esc(t('value'))}</th></tr></thead><tbody>${measured.sort((a,b)=>a.v-b.v).map(m=>`<tr><td><a href="${esc(charHref(m.d))}" data-tool-profile="${esc(m.d.slug)}">${esc(nameOf(m.d))}</a></td><td>${esc(fmt(m.v)+valueSuffix(key,basis))}</td></tr>`).join('')}</tbody></table></details>`;
}
function toolUpdate(id,fn){
  const focused=document.activeElement?.id; fn(); render(); if(focused===id) document.getElementById(id)?.focus();
}
function bindDistribution(){
  $('#distMetric').onchange=e=>toolUpdate('distMetric',()=>{state.distMetric=e.target.value;});
  $('#distBasis').onchange=e=>toolUpdate('distBasis',()=>{state.distBasis=e.target.value;});
  if($('#distTarget')) $('#distTarget').onchange=e=>{if(setTarget(e.target))toolUpdate('distTarget',()=>{});};
}

/* User weights affect exploration only. Default matching preserves the original rule. */
function matchesHTML(){
  const source=comparisonRecord(state.matchSource)||DATA[0],weights=state.matchWeights||Analysis.weights;
  const results=Analysis.matches(DATA,source,weights,state.matchBasis).slice(0,8);
  return `<div class="toolform"><label for="matchSource">${esc(t('sourceFigure'))}<select id="matchSource">${figureOptions(source.slug)}</select></label><label for="matchBasis">${esc(t('basis'))}<select id="matchBasis">${basisOptions(state.matchBasis)}</select></label><button class="btn" id="resetWeights">${esc(t('resetWeights'))}</button></div>
    <p class="toolnote">${esc(t('weightNote'))}</p><div class="weights">${METRIC_KEYS.map(key=>`<label for="weight-${key}">${esc(t(key))}<input class="toolinput" id="weight-${key}" data-weight="${key}" type="number" min="0" max="100" step="1" value="${Math.round(weights[key]*100)}"></label>`).join('')}</div>
    <p class="toolnote" id="distanceNote">${esc(t('distanceNote'))}</p>${results.length?`<table class="tooltable" aria-describedby="distanceNote"><thead><tr><th>${esc(t('name'))}</th><th>${esc(t('distance'))}</th><th></th></tr></thead><tbody>${results.map(m=>`<tr><td><a href="${esc(charHref(m.d))}" data-tool-profile="${esc(m.d.slug)}">${esc(nameOf(m.d))}</a></td><td>${fmt(m.score,3)}</td><td><button class="btn" data-match-pair="${esc(m.d.slug)}" data-source="${esc(source.slug)}">${esc(t('comparePair'))}</button></td></tr>`).join('')}</tbody></table>`:`<p role="status">${esc(t('noMatches'))}</p>`}`;
}
function bindMatches(){
  $('#matchSource').onchange=e=>toolUpdate('matchSource',()=>{state.matchSource=e.target.value;});
  $('#matchBasis').onchange=e=>toolUpdate('matchBasis',()=>{state.matchBasis=e.target.value;});
  $('#resetWeights').onclick=()=>toolUpdate('resetWeights',()=>{state.matchWeights=null;});
  $$('[data-weight]').forEach(input=>input.onchange=()=>{
    if(!input.checkValidity()){input.reportValidity();return;}
    toolUpdate(input.id,()=>{state.matchWeights={...(state.matchWeights||Analysis.weights),[input.dataset.weight]:+input.value/100};});
  });
}

/* Higher / Lower uses the same displayed precision as the answer. */
function newGameRound(){
  const key=state.gameMetric,basis=key==='height'?'raw':state.gameBasis;
  const pool=DATA.filter(d=>shownValue(d,key,basis)!=null);
  if(pool.length<2){gameRound=null;return;}
  const a=Math.floor(Math.random()*pool.length),rest=pool.filter((_,i)=>i!==a),b=Math.floor(Math.random()*rest.length);
  gameRound={left:pool[a].slug,right:rest[b].slug,key,basis,unit:state.unit,answer:null};
}
function gameHTML(){
  const key=state.gameMetric,basis=key==='height'?'raw':state.gameBasis;
  if(!gameRound||gameRound.key!==key||gameRound.basis!==basis||gameRound.unit!==state.unit)newGameRound();
  const round=gameRound;
  const figures=round?[bySlug.get(round.left),bySlug.get(round.right)]:[];
  return `<div class="toolform"><label for="gameMetric">${esc(t('metric'))}<select id="gameMetric">${metricOptions(key)}</select></label><label for="gameBasis">${esc(t('basis'))}<select id="gameBasis"${key==='height'?' disabled':''}>${basisOptions(basis)}</select></label><button class="btn" id="gameReset">${esc(t('gameReset'))}</button></div>
    <p class="toolnote">${esc(t('gameNote'))}</p><div class="toolstats"><span>${esc(t('gameScore'))}<strong>${gameScore.correct} / ${gameScore.total}</strong></span><span>${esc(t('streak'))}<strong>${gameScore.streak}</strong></span></div>
    ${!round?`<p>${esc(t('notEnough'))}</p>`:`<div class="gamepair">${figures.map((d,i)=>`<div class="gamefigure"><img src="${THUMB}/320/${d.official}.webp" width="90" height="140" alt=""><div><h3>${esc(nameOf(d))}</h3><div class="gamevalue">${i===0||round.answer?esc(valueText(d,key,basis)):'?'}</div></div></div>`).join('')}</div>
    <p class="gameresult" role="status">${round.answer?esc(t(round.correct?'correct':'incorrect')+' · '+t(round.outcome)):''}</p><div class="gameactions">${['higher','lower','equal'].map(k=>`<button class="btn" id="guess-${k}" data-guess="${k}"${round.answer?' disabled':''}>${esc(t(k))}</button>`).join('')}<button class="btn primary" id="nextRound"${!round.answer?' disabled':''}>${esc(t('nextRound'))}</button></div>`}`;
}
function bindGame(){
  $('#gameMetric').onchange=e=>toolUpdate('gameMetric',()=>{state.gameMetric=e.target.value;gameRound=null;});
  $('#gameBasis').onchange=e=>toolUpdate('gameBasis',()=>{state.gameBasis=e.target.value;gameRound=null;});
  $('#gameReset').onclick=()=>toolUpdate('gameReset',()=>{gameScore={correct:0,total:0,streak:0};gameRound=null;});
  $$('[data-guess]').forEach(b=>b.onclick=()=>{
    if(gameRound.answer)return;
    const left=bySlug.get(gameRound.left),right=bySlug.get(gameRound.right);
    const result=Analysis.outcome(shownValue(left,gameRound.key,gameRound.basis),shownValue(right,gameRound.key,gameRound.basis));
    gameRound.answer=b.dataset.guess;gameRound.outcome=result;gameRound.correct=result===b.dataset.guess;
    gameScore.total++;if(gameRound.correct){gameScore.correct++;gameScore.streak++;}else gameScore.streak=0;
    renderTool(filtered());$('#nextRound').focus();
  });
  if($('#nextRound'))$('#nextRound').onclick=()=>{newGameRound();renderTool(filtered());$('#guess-higher').focus();};
}

/* Fictional references never enter DATA, bySlug, exports or derived classifications. */
function sandboxHTML(){
  const s=state.sandbox||{},record=sandboxRecord();
  return `<p class="toolnote">${esc(t('sandboxNote'))}</p><form id="sandboxForm"><div class="sandboxfields"><label class="widename" for="sandboxName">${esc(t('sandboxName'))}<input class="toolinput" id="sandboxName" name="name" maxlength="40" value="${esc(s.name||'')}"></label>${METRIC_KEYS.map(key=>`<label for="sandbox-${key}">${esc(t(key))} (cm)<input class="toolinput" id="sandbox-${key}" name="${key}" type="number" min="${key==='height'?1:.1}" max="300" step="0.1"${key==='height'?' required':''} value="${s[Analysis.fields[key]]??''}"></label>`).join('')}</div><div class="sandboxactions"><button class="btn primary" type="submit">${esc(t('saveSandbox'))}</button>${record?`<button class="btn" type="button" id="addSandbox">${esc(t('addSandbox'))}</button><button class="btn" type="button" id="sandboxMatch">${esc(t('matches'))}</button><button class="btn" type="button" id="clearSandbox">${esc(t('clearSandbox'))}</button>`:''}</div></form><p class="toolnote">${esc(t('sandboxLinkNote'))}</p><p id="sandboxStatus" role="status"></p>`;
}
function bindSandbox(){
  $('#sandboxForm').onsubmit=e=>{
    e.preventDefault();
    const form=e.target,raw={name:form.elements.name.value};
    for(const key of METRIC_KEYS)raw[Analysis.fields[key]]=form.elements[key].value===''?null:Number(form.elements[key].value);
    const value=validSandbox(raw);
    if(!value){$('#sandboxStatus').textContent=t('sandboxHeight');return;}
    state.sandbox=value;render();$('#sandboxStatus').textContent=t('sandboxSaved');$('#addSandbox').focus();
  };
  if($('#addSandbox'))$('#addSandbox').onclick=()=>{if(!state.compare.includes(SANDBOX_SLUG))toggleCompare(SANDBOX_SLUG);};
  if($('#sandboxMatch'))$('#sandboxMatch').onclick=()=>openTool('matches',SANDBOX_SLUG);
  if($('#clearSandbox'))$('#clearSandbox').onclick=()=>{
    state.sandbox=null;state.compare=state.compare.filter(s=>s!==SANDBOX_SLUG);
    if(state.compareBase===SANDBOX_SLUG)state.compareBase='';if(state.matchSource===SANDBOX_SLUG)state.matchSource='';
    render();$('#sandboxName').focus();
  };
}
$('#toolsView').addEventListener('click',e=>{
  const profile=e.target.closest('[data-tool-profile]');
  if(profile && !(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)){e.preventDefault();openModal(profile.dataset.toolProfile);return;}
  const pair=e.target.closest('[data-match-pair]');
  if(pair){state.compare=[pair.dataset.source,pair.dataset.matchPair];state.compareBase=pair.dataset.source;state.compareMode=state.matchBasis;renderCompare();syncCardCompare();writeHash(true);openCompare();}
});
