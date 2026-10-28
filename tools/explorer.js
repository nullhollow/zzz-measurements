/* Exploration state is separate from the official roster and its derived rules. */
const TOOL_VIEWS=['distribution','matches','game','sandbox','lineup','guide'];
const METRIC_KEYS=['height','bust','underbust','waist','hip','thigh'];
const COMPARE_ROWS=['height','waist','hip','thigh','cup','bust','underbust','sizes','whr','whtr','shape','build','thighNote','figureRead'];
const DEFAULT_COMPARE_ROWS=['height','waist','hip','thigh','cup','bust','underbust','whr','whtr'];
const SANDBOX_SLUG='~sandbox';
let gameRound=null, gameScore={correct:0,total:0,streak:0};
function explorerDefaults(){
  return {lineupSlugs:defaultLineup(),lineupOrder:'custom',lineupReference:'ruler',lineupReferenceCm:170,guideMetric:'height',compareRows:null,compareBase:'',compareHeight:160,sandbox:null,matchSource:'',matchBasis:'raw',matchWeights:null,
    distMetric:'cup',distBasis:'raw',distCupView:'letters',distSelection:'',gameMetric:'waist',gameBasis:'raw'};
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
  if(Array.isArray(raw.lineupSlugs))out.lineupSlugs=[...new Set(raw.lineupSlugs.filter(s=>bySlug.has(s)))].slice(0,8);
  if(['custom','short','tall','faction'].includes(raw.lineupOrder))out.lineupOrder=raw.lineupOrder;
  if(['none','ruler','door','user'].includes(raw.lineupReference))out.lineupReference=raw.lineupReference;
  if(Number.isFinite(raw.lineupReferenceCm)&&raw.lineupReferenceCm>=1&&raw.lineupReferenceCm<=300)out.lineupReferenceCm=raw.lineupReferenceCm;
  if(['height','bust','underbust','waist','hip','thigh'].includes(raw.guideMetric))out.guideMetric=raw.guideMetric;
  out.sandbox=validSandbox(raw.sandbox);
  if(Array.isArray(raw.compareRows)){
    const rows=[...new Set(raw.compareRows.filter(k=>COMPARE_ROWS.includes(k)))];
    if(rows.length) out.compareRows=rows;
  }
  if(['letters','matrix'].includes(raw.distCupView))out.distCupView=raw.distCupView;
  if(typeof raw.distSelection==='string'&&/^(cup:[A-Z]{1,8}|size:\d{1,3}:[A-Z]{1,8}|bin:\d)$/.test(raw.distSelection))out.distSelection=raw.distSelection;
  if(typeof raw.compareBase==='string') out.compareBase=raw.compareBase;
  if(Number.isFinite(raw.compareHeight)&&raw.compareHeight>=1&&raw.compareHeight<=300) out.compareHeight=Number(raw.compareHeight.toFixed(1));
  if(bySlug.has(raw.matchSource)||raw.matchSource===SANDBOX_SLUG&&out.sandbox) out.matchSource=raw.matchSource;
  for(const key of ['matchBasis','gameBasis']) if(['raw','height'].includes(raw[key])) out[key]=raw[key];
  if(['raw','height','scaled'].includes(raw.distBasis)) out.distBasis=raw.distBasis;
  for(const key of ['distMetric','gameMetric']) if(['cup',...METRIC_KEYS].includes(raw[key])) out[key]=raw[key];
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
function figurePicker(id,records,selected,label,optional=false){
  const sorted=[...records].sort((a,b)=>nameOf(a).localeCompare(nameOf(b),state.lang));
  const current=records.find(d=>d.slug===selected);
  return `<label for="${id}">${esc(label)}<input class="toolinput figurepicker" type="search" id="${id}" list="${id}-options" autocomplete="off" value="${esc(current?nameOf(current):'')}" placeholder="${esc(t(optional?'noReference':'searchFigure'))}"${optional?'':' required'}><datalist id="${id}-options">${sorted.map(d=>`<option value="${esc(nameOf(d))}">${esc(d.slug)}</option>`).join('')}</datalist></label>`;
}
function bindFigurePicker(id,records,fn,optional=false){
  const input=document.getElementById(id);
  input.oninput=()=>input.setCustomValidity('');
  input.onchange=()=>{
    const value=input.value.trim().toLocaleLowerCase(state.lang);
    const d=records.find(d=>[nameOf(d),d.display,d.name,d.slug,d.name_ja,d.name_zh].some(n=>n&&n.toLocaleLowerCase(state.lang)===value));
    if(!d&&!(optional&&!value)){input.setCustomValidity(t('chooseKnownFigure'));input.reportValidity();return;}
    requestAnimationFrame(()=>{
      const nextId=document.activeElement?.id;fn(d?.slug||'');
      if(nextId)document.getElementById(nextId)?.focus();
    });
  };
}
function shownValue(record,key,basis='raw'){
  const v=Analysis.value(record,key,basis,state.compareHeight);
  return v==null?null:(basis==='height'&&key!=='height'?v:toDisp(v));
}
function valueSuffix(key,basis){ return basis==='height'&&key!=='height'?'%':USUF(); }
function valueText(d,key,basis){ const v=shownValue(d,key,basis); return v==null?'—':fmt(v,isCm()&&(basis==='raw'||key==='height')?(d.precision_cm||1):1)+valueSuffix(key,basis); }
function targetControl(id){
  return `<label for="${id}">${esc(t('targetHeight'))}<input class="toolinput" id="${id}" type="number" min="1" max="300" step="0.1" value="${state.compareHeight}" required></label>`;
}
function setTarget(input){
  if(!input.checkValidity()){ input.reportValidity(); return false; }
  state.compareHeight=+input.value; return true;
}
function pageHref(tools,params,view){
  const p=new URLSearchParams(params);
  p.set('unit',state.unit);p.set('cups',state.cupSystem);
  p.set('lang',state.lang);p.set('th',siteTheme.preference);
  if(tools){
    if(!TOOLS_PAGE && ['table','plot'].includes(state.view))p.set('from',state.view);
    p.set('view',view||'distribution');
  }else{
    const roster=p.get('from');p.delete('from');
    if(TOOL_VIEWS.includes(p.get('view'))){if(['table','plot'].includes(roster))p.set('view',roster);else p.delete('view');}
  }
  return (tools?'tools.html':'index.html')+(p.size?'#'+p.toString():'');
}
function syncPageLinks(params){
  $('#measurementsLink').href=pageHref(false,params);
  $('#chooseAgents').href=pageHref(false,params);
  $('#toolsLink').href=pageHref(true,params,TOOL_VIEWS.includes(state.view)?state.view:'distribution');
  const favouriteParams=new URLSearchParams(params);favouriteParams.set('lang',state.lang);favouriteParams.set('th',siteTheme.preference);
  $('#favouritesLink').href='favourites.html#'+favouriteParams;
  $$('#toolsNav [data-tool-link]').forEach(a=>a.href=pageHref(true,params,a.dataset.toolLink));
}
function openTool(view,source){
  if(!TOOL_VIEWS.includes(view)) return;
  if($('#overlay').classList.contains('open')) closeModal();
  if(source) state.matchSource=source;
  if(!TOOLS_PAGE){writeHash(true);location.href=pageHref(true,new URLSearchParams(location.hash.slice(1)),view);return;}
  const changed=state.view!==view;
  state.view=view; writeHash(!changed); render(true);
  $('#toolTitle').focus({preventScroll:true});
  $('#toolsView').scrollIntoView({block:'start',behavior:'instant'});
}
$('#toolsNav')?.addEventListener('click',e=>{
  const a=e.target.closest('[data-tool-link]');
  if(a && !(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)){e.preventDefault();openTool(a.dataset.toolLink);}
});
window.addEventListener('resize',debounce(()=>{if(state.view==='distribution')renderTool(filtered());},150));
if(TOOLS_PAGE){
  const shell=$('.tools-shell');
  new ResizeObserver(()=>document.documentElement.style.setProperty('--tools-offset',shell.offsetHeight+'px')).observe(shell);
}
$('#toolSelect')?.addEventListener('change',e=>openTool(e.target.value));
function renderTool(list){
  const root=$('#toolsView');document.body.dataset.toolView=state.view;
  if($('#toolSelect')){$('#toolSelect').value=state.view;$('#toolSelect').setAttribute('aria-label',t('tools'));}
  const content=state.view==='lineup'?lineupHTML():state.view==='guide'?guideHTML():state.view==='distribution'?distributionHTML(list):state.view==='matches'?matchesHTML():state.view==='game'?gameHTML():sandboxHTML();
  root.innerHTML=`<div class="toolhead"><h2 id="toolTitle" tabindex="-1">${esc(t(state.view))}</h2></div>${content}`;
  if(state.view==='lineup')bindLineup();
  else if(state.view==='guide')bindGuide();
  else if(state.view==='distribution') bindDistribution();
  else if(state.view==='matches') bindMatches();
  else if(state.view==='game') bindGame();
  else bindSandbox();
}

/* Comparison rows, reference differences and same-height equivalents. */
function rowLabel(key){ return key==='sizes'?'UK / US / EU':t(key==='whr'?'waistHip':key==='whtr'?'waistHeight':key); }
function comparisonText(d,key,basis){
  if(METRIC_KEYS.includes(key)){
    const text=valueText(d,key,basis);
    return key==='height'?text+heightNote(d):text;
  }
  if(key==='cup')return d.temporary?'—':cupText(d);
  if(key==='sizes')return d.temporary?'—':`${d.uk} / ${d.us} / ${d.eu}`;
  if(key==='whr'||key==='whtr')return fmtPct(d[key]);
  if(d.temporary)return '—';
  if(key==='figureRead')return readFor(d)||'—';
  if(key==='thighNote')return tagText(tagsFor(d).thighs);
  return tagText(tagsFor(d)[key==='build'?'balance':key])||'—';
}
function openCompare(){
  const active=document.activeElement, focusId=active?.id, focusMode=active?.dataset.compareMode;
  const pickerOpen=$('#rowPicker')?.open||false;
  const list=state.compare.map(comparisonRecord).filter(Boolean);
  if(list.length<2){ toast(t('pickTwo')); return; }
  if(!state.compare.includes(state.compareBase)) state.compareBase='';
  const reference=comparisonRecord(state.compareBase), basis=state.compareMode;
  const rowKeys=(state.compareRows||DEFAULT_COMPARE_ROWS).filter(k=>!(basis==='height'&&k==='whtr'&&!state.compareRows));
  const numeric=(d,key)=>METRIC_KEYS.includes(key)?shownValue(d,key,basis):['whr','whtr'].includes(key)?d[key]??null:null;
  const best={height:'max',waist:'min',hip:'max',thigh:'max',cup:'max'};
  const body=rowKeys.map(key=>{
    const vals=list.map(d=>key==='cup'?(d.temporary?null:cupScore(d)):numeric(d,key));
    // Raw winners retain the original centimetre rule. Adjusted modes share visible ties.
    const ranked=vals.map((v,i)=>v==null?null:key==='cup'?v:key==='height'||basis==='raw'?Analysis.value(list[i],key,'raw'):Analysis.displayed(v));
    const nums=ranked.filter(v=>v!=null), target=nums.length?(best[key]==='min'?Math.min(...nums):Math.max(...nums)):null;
    const direction=best[key]?` <span class="cmpdir" title="${esc(t(best[key]==='min'?'smallerWins':'largerWins'))}">${best[key]==='min'?'↓':'↑'}</span>`:'';
    return `<tr data-metric="${key}"><th scope="row"><button class="metric-help" data-help="${key==='cup'||key==='sizes'?'cup':['whr','whtr'].includes(key)?'ratio':'overview'}">${esc(rowLabel(key))}</button>${direction}</th>${list.map((d,i)=>{
      let delta='';
      if(reference && d.slug!==reference.slug && key!=='cup'){
        const decimals=['whr','whtr'].includes(key)?3:isCm()&&(basis==='raw'||key==='height')?Math.max(...list.map(d=>d.precision_cm||1)):1;
        const a=vals[i],b=numeric(reference,key);
        const diff=Analysis.difference(a==null?null:Number(a.toFixed(decimals)),b==null?null:Number(b.toFixed(decimals)));
        const suffix=decimals===3?'':basis==='height'&&key!=='height'?' '+t('pp'):USUF();
        if(diff!=null){ const rounded=Number(diff.toFixed(decimals)); delta=`<small class="cmpdelta">${rounded>0?'+':''}${fmt(rounded,decimals)}${esc(suffix)}</small>`; }
      }
      return `<td class="${best[key]&&ranked[i]!=null&&ranked[i]===target?'win':''}${key==='figureRead'?' cmdesc':''}">${esc(comparisonText(d,key,basis))}${delta}</td>`;
    }).join('')}</tr>`;
  }).join('');
  const selected=state.compareRows||DEFAULT_COMPARE_ROWS, options=[...selected,...COMPARE_ROWS.filter(k=>!selected.includes(k))];
  const rowPicker=`<details class="rowpicker" id="rowPicker"${pickerOpen?' open':''}><summary>${esc(t('rows'))}</summary><div class="rowoptions">${options.map(key=>{
    const index=selected.indexOf(key);
    return `<div class="rowoption"><label><input type="checkbox" id="row-${key}" data-row="${key}"${index>=0?' checked':''}>${esc(rowLabel(key))}</label><button class="btn" id="up-${key}" data-move="${key}" data-direction="-1"${index<=0?' disabled':''} aria-label="${esc(t('moveUp')+': '+rowLabel(key))}">↑</button><button class="btn" id="down-${key}" data-move="${key}" data-direction="1"${index<0||index===selected.length-1?' disabled':''} aria-label="${esc(t('moveDown')+': '+rowLabel(key))}">↓</button></div>`;
  }).join('')}</div><button class="btn" id="restoreRows">${esc(t('restoreRows'))}</button></details>`;
  $('#modal').innerHTML=`<button class="x" id="closeModal" aria-label="${esc(t('close'))}">✕</button>
    <div class="mhead"><h2 id="mTitle">${esc(t('compareTitle'))}</h2><button class="btn" id="modalSettings" data-open-settings>${esc(t('settingsButton'))}</button><button class="btn" id="compareSaved">${esc(t('savedComparisons'))}</button><button class="btn" id="exportCompare">${esc(t('exportComparison'))}</button><div class="sub2">${list.length} ${esc(t('picked'))}</div>
      <div class="cmpcontrols"><div class="seg" role="group" aria-label="${esc(t('compareBasis'))}">${['raw','height','scaled'].map(k=>`<button id="basis-${k}" data-compare-mode="${k}" aria-pressed="${basis===k}">${esc(t(k==='raw'?'rawMeasurements':k==='height'?'heightAdjusted':'sameHeight'))}</button>`).join('')}</div>
      ${basis==='scaled'?targetControl('compareTarget'):''}
      ${figurePicker('compareReference',list,state.compareBase,t('reference'),true)}
      ${basis!=='raw'?`<p class="fnote" id="compareBasisNote">${esc(t(basis==='height'?'heightAdjustedNote':'scaledNote'))}</p>`:''}${state.cupSystem!=='uk'?`<p class="fnote">${esc(t('cupRankNote'))}</p>`:''}${rowPicker}<div class="compare-edit">${list.map((d,i)=>figurePicker('replaceAgent'+i,DATA.filter(x=>x.slug===d.slug||!state.compare.includes(x.slug)),d.slug,t('replaceAgent')+': '+nameOf(d))).join('')}${list.length<4?figurePicker('addAgent',DATA.filter(d=>!state.compare.includes(d.slug)),'',t('addAgent')):''}</div></div></div>
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
  bindFigurePicker('compareReference',list,slug=>{state.compareBase=slug;update();},true);
  list.forEach((d,i)=>bindFigurePicker('replaceAgent'+i,DATA.filter(x=>x.slug===d.slug||!state.compare.includes(x.slug)),slug=>{if(!slug||state.compare.includes(slug))return;state.compare[i]=slug;renderCompare();update();}));
  if($('#addAgent'))bindFigurePicker('addAgent',DATA.filter(d=>!state.compare.includes(d.slug)),slug=>{if(slug&&state.compare.length<4&&!state.compare.includes(slug)){state.compare.push(slug);renderCompare();update();}});
  $('#compareSaved').onclick=openSavedComparisons;
  $('#exportCompare').onclick=exportComparison;
  if($('#compareTarget')) $('#compareTarget').onchange=e=>{if(setTarget(e.target)) update();};
  $$('#modal [data-row]').forEach(input=>input.onchange=()=>{
    const chosen=[...(state.compareRows||DEFAULT_COMPARE_ROWS)];
    if(input.checked) chosen.push(input.dataset.row);
    else {if(chosen.length===1){input.checked=true;toast(t('keepRow'));return;} chosen.splice(chosen.indexOf(input.dataset.row),1);}
    state.compareRows=chosen;update();
  });
  $$('#modal [data-move]').forEach(b=>b.onclick=()=>{
    const chosen=[...(state.compareRows||DEFAULT_COMPARE_ROWS)],a=chosen.indexOf(b.dataset.move),z=a+Number(b.dataset.direction);
    if(a<0||z<0||z>=chosen.length)return;
    [chosen[a],chosen[z]]=[chosen[z],chosen[a]];state.compareRows=chosen;update();
  });
  $('#restoreRows').onclick=()=>{state.compareRows=null;update();};
}

/* Saved groups are local preferences, never roster records. */
const SAVED_COMPARISONS='zzz-comparisons-v1';
function validSavedComparison(raw){
  if(!raw||typeof raw!=='object'||typeof raw.name!=='string'||!raw.name.trim()||raw.name.length>60)return null;
  const sandbox=validSandbox(raw.sandbox);
  if(!Array.isArray(raw.compare))return null;
  const compare=[...new Set(raw.compare.filter(slug=>bySlug.has(slug)||slug===SANDBOX_SLUG&&sandbox))].slice(0,4);
  if(compare.length<2)return null;
  const rows=Array.isArray(raw.compareRows)?[...new Set(raw.compareRows.filter(k=>COMPARE_ROWS.includes(k)))]:null;
  return {name:raw.name.trim(),compare,sandbox:compare.includes(SANDBOX_SLUG)?sandbox:null,
    compareRows:rows?.length?rows:null,compareBase:compare.includes(raw.compareBase)?raw.compareBase:'',
    compareMode:['height','scaled'].includes(raw.compareMode)?raw.compareMode:'raw',
    compareHeight:Number.isFinite(raw.compareHeight)&&raw.compareHeight>=1&&raw.compareHeight<=300?raw.compareHeight:160,
    unit:raw.unit==='in'?'in':'cm',cupSystem:['uk','us','eu'].includes(raw.cupSystem)?raw.cupSystem:'uk'};
}
function savedComparisons(){
  try{
    const raw=localStorage.getItem(SAVED_COMPARISONS);if(!raw||raw.length>100000)return [];
    const parsed=JSON.parse(raw);return Array.isArray(parsed)?parsed.slice(0,20).map(validSavedComparison).filter(Boolean):[];
  }catch(_){return [];}
}
function storeComparisons(groups){
  try{localStorage.setItem(SAVED_COMPARISONS,JSON.stringify(groups));return true;}
  catch(_){$('#savedStatus').textContent=t('storageUnavailable');return false;}
}
let savedTrigger=null,removedComparison=null;
function openSavedComparisons(){
  if($('#savedDialog').open)return;
  savedTrigger=document.activeElement;removedComparison=null;renderSavedComparisons();
  $('#savedDialog').showModal();document.body.classList.add('modal-open');
  ($('#comparisonName')||$('#savedClose')).focus();
}
function closeSavedComparisons(){
  $('#savedDialog').close();
  if(!$('#overlay').classList.contains('open'))document.body.classList.remove('modal-open');
  (savedTrigger?.isConnected?savedTrigger:$('#savedCompareBtn')).focus();
}
function renderSavedComparisons(){
  const groups=savedComparisons(),canSave=state.compare.length>=2;
  $('#savedDialog').innerHTML=`<button class="settings-close btn" id="savedClose" aria-label="${esc(t('close'))}">✕</button><h2 id="savedTitle">${esc(t('savedComparisons'))}</h2>
    ${canSave?`<form id="saveComparisonForm"><label for="comparisonName">${esc(t('comparisonName'))}</label><div class="savedform"><input class="toolinput" id="comparisonName" maxlength="60" required autocomplete="off"><button class="btn primary" type="submit">${esc(t('saveComparison'))}</button></div></form>`:''}
    <p class="toolnote">${esc(t('savedLocal'))}</p><div class="savedgroups">${groups.length?groups.map((g,i)=>`<div class="savedgroup"><span>${esc(g.name)}</span><button class="btn" data-load-comparison="${i}" aria-label="${esc(t('loadComparison')+': '+g.name)}">${esc(t('loadComparison'))}</button><button class="btn" data-delete-comparison="${i}" aria-label="${esc(t('deleteComparison')+': '+g.name)}">${esc(t('deleteComparison'))}</button></div>`).join(''):`<p>${esc(t('noSavedComparisons'))}</p>`}</div><p id="savedStatus" role="status"></p>${removedComparison?`<button class="btn" id="undoComparison">${esc(t('undoDelete'))}</button>`:''}`;
  $('#savedClose').onclick=closeSavedComparisons;
  if(canSave)$('#saveComparisonForm').onsubmit=e=>{
    e.preventDefault();const name=$('#comparisonName').value.trim();if(!name)return;
    const group=validSavedComparison({...state,name}),items=savedComparisons(),index=items.findIndex(g=>g.name===name);
    if(index<0&&items.length>=20){$('#savedStatus').textContent=t('savedLimit');return;}
    if(index<0)items.push(group);else items[index]=group;
    if(storeComparisons(items)){renderSavedComparisons();$('#savedStatus').textContent=t('comparisonSaved');$('#comparisonName').focus();}
  };
  $$('#savedDialog [data-load-comparison]').forEach(b=>b.onclick=()=>{
    const group=savedComparisons()[+b.dataset.loadComparison];if(!group)return;
    const {name,sandbox,...settings}=group;Object.assign(state,settings);if(sandbox)state.sandbox=sandbox;
    try{localStorage.setItem('zzz-unit',state.unit);localStorage.setItem('zzz-cup-system',state.cupSystem);}catch(_){}
    closeSavedComparisons();syncControls();renderFilterPanel();render();openCompare();
  });
  $$('#savedDialog [data-delete-comparison]').forEach(b=>b.onclick=()=>{
    const items=savedComparisons(),removed=items.splice(+b.dataset.deleteComparison,1)[0];
    if(storeComparisons(items)){removedComparison=removed;renderSavedComparisons();$('#undoComparison').focus();}
  });
  if($('#undoComparison'))$('#undoComparison').onclick=()=>{
    const items=savedComparisons();if(items.length>=20){$('#savedStatus').textContent=t('savedLimit');return;}
    items.push(removedComparison);if(storeComparisons(items)){removedComparison=null;renderSavedComparisons();$('#savedClose').focus();}
  };
}
$('#savedCompareBtn').onclick=openSavedComparisons;
$('#savedDialog').addEventListener('cancel',e=>{e.preventDefault();closeSavedComparisons();});
$('#savedDialog').addEventListener('click',e=>{if(e.target===e.currentTarget){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeSavedComparisons();}});
function csvText(rows){
  const cell=value=>{
    let text=value==null?'':String(value);
    if(typeof value==='string'&&/^[\s]*[=+@-]/.test(text))text="'"+text;
    return '"'+text.replaceAll('"','""')+'"';
  };
  return '\uFEFF'+rows.map(row=>row.map(cell).join(',')).join('\r\n')+'\r\n';
}
function exportComparison(){
  const selected=state.compare.map(comparisonRecord).filter(Boolean),list=selected.filter(d=>!d.temporary),basis=state.compareMode;
  const chosenReference=comparisonRecord(state.compareBase),reference=chosenReference?.temporary?null:chosenReference;
  const keys=(state.compareRows||DEFAULT_COMPARE_ROWS).filter(k=>!(basis==='height'&&k==='whtr'&&!state.compareRows));
  const rows=[['character_slug','character','measurement','value','unit','reference_slug','difference','difference_unit','basis','cup_system','reference_height_cm']];
  for(const key of keys)for(const d of list){
    const numeric=METRIC_KEYS.includes(key)||['whr','whtr'].includes(key),decimals=METRIC_KEYS.includes(key)?1:3;
    const value=record=>METRIC_KEYS.includes(key)?shownValue(record,key,basis):record[key]??null;
    const shown=record=>{const v=value(record);return v==null?null:Number(v.toFixed(decimals));};
    const unit=METRIC_KEYS.includes(key)?basis==='height'&&key!=='height'?'%':state.unit:'';
    const delta=reference&&d.slug!==reference.slug&&numeric?Analysis.difference(shown(d),shown(reference)):null;
    rows.push([d.slug,nameOf(d),key,numeric?shown(d):comparisonText(d,key,basis),unit,reference?.slug||'',delta==null?null:Number(delta.toFixed(decimals)),delta==null?'':unit==='%'?'pp':unit,basis,state.cupSystem,basis==='scaled'?state.compareHeight:'']);
  }
  const url=URL.createObjectURL(new Blob([csvText(rows)],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');
  a.href=url;a.download='zzz-comparison.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  toast(t(selected.length===list.length?'comparisonExported':'comparisonExportedCanonical'));
}

function distributionOptions(key){
  return `<option value="cup"${key==='cup'?' selected':''}>${esc(cupSizeLabel())}</option>`+metricOptions(key);
}
function distributionResults(records,label,value){
  const selected=!!state.distSelection;
  const rows=records.map(d=>`<tr><td><a href="${esc(charHref(d))}" data-tool-profile="${esc(d.slug)}">${esc(nameOf(d))}</a></td><td>${esc(value(d))}</td><td><button class="btn" id="dist-add-${esc(d.slug)}" data-dist-add="${esc(d.slug)}" aria-pressed="${state.compare.includes(d.slug)}" aria-label="${esc((state.compare.includes(d.slug)?t('removeFromCompare'):t('addCompare'))+': '+nameOf(d))}">${esc(t(state.compare.includes(d.slug)?'added':'cmpShort'))}</button></td></tr>`).join('');
  const table=`<table class="tooltable"><thead><tr><th scope="col">${esc(t('name'))}</th><th scope="col">${esc(t('value'))}</th><th scope="col"><span class="sr">${esc(t('compare'))}</span></th></tr></thead><tbody>${rows}</tbody></table>`;
  return selected?`<section class="distresults" id="distResults" aria-labelledby="distResultTitle"><div class="selectionhead"><h3 id="distResultTitle" tabindex="-1">${esc(label)} · ${records.length} ${esc(t('entries'))}</h3><button class="btn" id="clearDistribution">${esc(t('showAllValues'))}</button></div>${table}</section>`:`<details class="tooldata"><summary>${esc(t('dataTable'))}</summary>${table}</details>`;
}
function barAttributes(selection,label,count){
  return count?`class="histbutton" role="button" tabindex="0" data-dist-select="${esc(selection)}" aria-pressed="${state.distSelection===selection}" aria-label="${esc(label+': '+count)}"`:'';
}
function cupDistributionHTML(list){
  const system=state.cupSystem,summary=Analysis.cupDistribution(list,system),counts=new Map(summary.bins.map(b=>[b.cup,b.count]));
  const bins=Analysis.cupDistribution(DATA,system).bins.map(b=>({cup:b.cup,count:counts.get(b.cup)||0}));
  const measured=list.map(d=>({d,s:Analysis.sizeParts(d[system])})).filter(x=>x.s).sort((a,b)=>bins.findIndex(g=>g.cup===a.s.cup)-bins.findIndex(g=>g.cup===b.s.cup)||cupScore(a.d)-cupScore(b.d));
  const markers=state.compare.map(comparisonRecord).filter(Boolean).map(d=>({d,s:Analysis.sizeParts(d[system])})).filter(x=>x.s);
  const width=innerWidth<=700?460:920,step=(width-80)/bins.length,x=cup=>40+(bins.findIndex(b=>b.cup===cup)+.5)*step;
  const peak=Math.max(1,...bins.map(b=>b.count)),rotate=innerWidth<=700&&system==='us';
  let chart;
  if(state.distCupView==='matrix'){
    const matrix=Analysis.cupMatrix(DATA,system),filteredMatrix=Analysis.cupMatrix(list,system);
    const cells=new Map(filteredMatrix.cells.map(c=>[c.band+':'+c.cup,c.slugs.length]));
    chart=`<div class="matrixwrap" role="region" tabindex="0" aria-label="${esc(t('bandByCup')+' ('+cupSystemName()+')')}"><table class="cupmatrix"><caption>${esc(t('bandByCup')+' ('+cupSystemName()+')')}</caption><thead><tr><th scope="col">${esc(t('sourceBand'))}</th>${matrix.cups.map(cup=>`<th scope="col">${esc(cup)}</th>`).join('')}</tr></thead><tbody>${matrix.bands.map(band=>`<tr><th scope="row">${band}</th>${matrix.cups.map(cup=>{const count=cells.get(band+':'+cup)||0,selection='size:'+band+':'+cup;return `<td>${count?`<button class="matrixcell" data-dist-select="${selection}" aria-pressed="${state.distSelection===selection}" aria-label="${esc(cupSystemName()+' '+band+cup+': '+count)}">${count}</button>`:'<span class="matrixempty">0</span>'}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
  }else{
    chart=`<svg class="histogram cuphistogram" viewBox="0 0 ${width} ${rotate?390:355}" role="group" aria-labelledby="histTitle histDesc"><title id="histTitle">${esc(cupSizeLabel())}</title><desc id="histDesc">${esc(t('population')+': '+summary.count+'. '+t('mostCommon')+': '+summary.modes.join(' / '))}</desc><line class="axis" x1="30" y1="290" x2="${width-30}" y2="290"/>${bins.map(b=>{const h=b.count/peak*205;return `<g ${barAttributes('cup:'+b.cup,b.cup,b.count)}><title>${esc(b.cup+': '+b.count)}</title><rect class="hit" x="${x(b.cup)-step*.48}" y="70" width="${step*.96}" height="255"/><rect class="bar" x="${x(b.cup)-step*.4}" y="${290-h}" width="${step*.8}" height="${h}"/><text x="${x(b.cup)}" y="${282-h}" text-anchor="middle">${b.count}</text><text class="cupcategory" x="${x(b.cup)}" y="318"${rotate?` transform="rotate(-45 ${x(b.cup)} 318)"`:''} text-anchor="${rotate?'end':'middle'}">${esc(b.cup)}</text></g>`;}).join('')}${markers.map((m,i)=>`<g class="chartmarker"><line class="marker halo" x1="${x(m.s.cup)}" x2="${x(m.s.cup)}" y1="${25+i*18}" y2="300"/><line class="marker" x1="${x(m.s.cup)}" x2="${x(m.s.cup)}" y1="${25+i*18}" y2="300"/><text class="markerlabel" x="${x(m.s.cup)}" y="${19+i*18}" text-anchor="middle">${i+1}</text></g>`).join('')}</svg>`;
  }
  const parts=state.distSelection.split(':'),selected=measured.filter(m=>parts[0]==='cup'?m.s.cup===parts[1]:parts[0]==='size'?m.s.band===+parts[1]&&m.s.cup===parts[2]:true);
  const label=parts[0]==='cup'?cupSystemName()+' '+parts[1]:parts[0]==='size'?cupSystemName()+' '+parts[1]+parts[2]:cupSizeLabel();
  return `<div class="toolform"><label for="distMetric">${esc(t('metric'))}<select id="distMetric">${distributionOptions('cup')}</select></label><label for="distCupView">${esc(t('chartView'))}<select id="distCupView"><option value="letters"${state.distCupView==='letters'?' selected':''}>${esc(t('cupLetters'))}</option><option value="matrix"${state.distCupView==='matrix'?' selected':''}>${esc(t('bandByCup'))}</option></select></label></div><p class="toolnote">${esc(t('cupDistributionNote').replace('{system}',cupSystemName()))}</p>${measured.some(m=>m.d[system]?.startsWith('≈'))?`<p class="toolnote">${esc(t('estimatedSizesNote'))}</p>`:''}${summary.count?`<div class="toolstats"><span>${esc(t('population'))}<strong>${summary.count}</strong></span><span>${esc(t('mostCommon'))}<strong>${esc(summary.modes.join(' / '))}</strong></span></div>${chart}<div class="markerlist">${markers.map((m,i)=>`<span>${i+1}. ${esc(nameOf(m.d))}: ${esc(cupText(m.d))}</span>`).join('')}</div>`:`<p>${esc(t('noValues'))}</p>`}${distributionResults(selected.map(m=>m.d),label,cupText)}`;
}

/* Filtered roster distribution; references are markers, never observations. */
function distributionHTML(list){
  if(state.distMetric==='cup')return cupDistributionHTML(list);
  const key=state.distMetric,basis=key==='height'?'raw':state.distBasis;
  const measured=list.map(d=>({d,v:shownValue(d,key,basis)})).filter(x=>x.v!=null);
  const summary=Analysis.distribution(measured.map(x=>x.v));
  const markers=state.compare.map(comparisonRecord).filter(Boolean).map(d=>({d,v:shownValue(d,key,basis)})).filter(x=>x.v!=null);
  let chart='';
  if(summary.count){
    const all=[...measured,...markers].map(x=>x.v),min=Math.min(...all),max=Math.max(...all),span=max-min||1;
    const width=innerWidth<=700?460:920;
    const x=v=>max===min?width/2:65+(v-min)/span*(width-130),base=290,peak=Math.max(...summary.bins.map(b=>b.count));
    const bars=summary.bins.map((b,i)=>{
      const left=x(b.lo),right=x(b.hi),barWidth=summary.bins.length===1?100:Math.max(1,right-left-3),cx=summary.bins.length===1?left:(left+right)/2;
      const bx=summary.bins.length===1?left-50:left,h=b.count/peak*205,label=fmt(b.lo)+'–'+fmt(b.hi)+valueSuffix(key,basis);
      return `<g ${barAttributes('bin:'+i,label,b.count)}><title>${esc(label+': '+b.count)}</title><rect class="hit" x="${bx}" y="70" width="${barWidth}" height="230"/><rect class="bar" x="${bx}" y="${base-h}" width="${barWidth}" height="${h}"/><text x="${cx}" y="${base-h-8}" text-anchor="middle">${b.count}</text></g>`;
    }).join('');
    chart=`<svg class="histogram" viewBox="0 0 ${width} 355" role="group" aria-labelledby="histTitle histDesc"><title id="histTitle">${esc(t('distribution')+': '+t(key))}</title><desc id="histDesc">${esc(t('population')+': '+summary.count+'. '+t('median')+': '+fmt(summary.median)+valueSuffix(key,basis))}</desc><line class="axis" x1="40" y1="290" x2="${width-35}" y2="290"/>${bars}<line class="median halo chartmarker" x1="${x(summary.median)}" x2="${x(summary.median)}" y1="60" y2="300"/><line class="median chartmarker" x1="${x(summary.median)}" x2="${x(summary.median)}" y1="60" y2="300"><title>${esc(t('median'))}</title></line>${markers.map((m,i)=>`<g class="chartmarker"><line class="marker halo" x1="${x(m.v)}" x2="${x(m.v)}" y1="${25+i*18}" y2="300"/><line class="marker" x1="${x(m.v)}" x2="${x(m.v)}" y1="${25+i*18}" y2="300"/><text x="${x(m.v)}" y="${19+i*18}" text-anchor="middle">${i+1}</text></g>`).join('')}<text x="${x(min)}" y="325" text-anchor="middle">${esc(fmt(min)+(min===max?valueSuffix(key,basis):''))}</text>${min===max?'':`<text x="${x(max)}" y="325" text-anchor="middle">${esc(fmt(max)+valueSuffix(key,basis))}</text>`}</svg>`;
  }
  const index=state.distSelection.startsWith('bin:')?+state.distSelection.split(':')[1]:-1,bin=summary.bins[index];
  const selected=bin?measured.filter(m=>Analysis.binIndex(m.v,summary.bins)===index):measured;
  const label=bin?fmt(bin.lo)+'–'+fmt(bin.hi)+valueSuffix(key,basis):t(key);
  return `<div class="toolform"><label for="distMetric">${esc(t('metric'))}<select id="distMetric">${distributionOptions(key)}</select></label><label for="distBasis">${esc(t('basis'))}<select id="distBasis"${key==='height'?' disabled':''}>${basisOptions(basis,true)}</select></label>${basis==='scaled'?targetControl('distTarget'):''}</div>
    <p class="toolnote">${esc(t('distributionNote'))}</p>${summary.count?`<div class="toolstats"><span>${esc(t('population'))}<strong>${summary.count}</strong></span><span>${esc(t('median'))}<strong>${esc(fmt(summary.median)+valueSuffix(key,basis))}</strong></span></div>${chart}<div class="markerlist">${markers.map((m,i)=>`<span>${i+1}. ${esc(nameOf(m.d))}: ${esc(fmt(m.v)+valueSuffix(key,basis))}</span>`).join('')}</div>`:`<p>${esc(t('noValues'))}</p>`}${distributionResults(selected.sort((a,b)=>a.v-b.v).map(m=>m.d),label,d=>valueText(d,key,basis))}`;
}
function toolUpdate(id,fn){
  const focused=document.activeElement?.id;fn();render();if(focused===id)document.getElementById(id)?.focus();
}
function bindDistribution(){
  $('#distMetric').onchange=e=>toolUpdate('distMetric',()=>{state.distMetric=e.target.value;state.distSelection='';});
  if($('#distCupView'))$('#distCupView').onchange=e=>toolUpdate('distCupView',()=>{state.distCupView=e.target.value;state.distSelection='';});
  if($('#distBasis'))$('#distBasis').onchange=e=>toolUpdate('distBasis',()=>{state.distBasis=e.target.value;state.distSelection='';});
  if($('#distTarget'))$('#distTarget').onchange=e=>{if(setTarget(e.target))toolUpdate('distTarget',()=>{state.distSelection='';});};
  if($('#clearDistribution'))$('#clearDistribution').onclick=()=>{state.distSelection='';render();$('#distMetric').focus();};
  $$('[data-dist-select]').forEach(b=>{
    const select=()=>{state.distSelection=b.dataset.distSelect;render();$('#distResultTitle').focus();$('#distResults').scrollIntoView({block:'start'});};
    b.onclick=select;
    if(b.tagName.toLowerCase()==='g')b.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};
  });
  $$('[data-dist-add]').forEach(b=>b.onclick=()=>{const id=b.id;toggleCompare(b.dataset.distAdd);document.getElementById(id)?.focus();});
}

/* User weights affect exploration only. Default matching preserves the original rule. */
function matchesHTML(){
  const source=comparisonRecord(state.matchSource)||DATA[0],weights=state.matchWeights||Analysis.weights;
  const results=Analysis.matches(DATA,source,weights,state.matchBasis).slice(0,8);
  const records=[...DATA,...(state.sandbox?[sandboxRecord()]:[])];
  return `<div class="toolform">${figurePicker('matchSource',records,source.slug,t('sourceFigure'))}<label for="matchBasis">${esc(t('basis'))}<select id="matchBasis">${basisOptions(state.matchBasis)}</select></label><button class="btn" id="resetWeights">${esc(t('resetWeights'))}</button></div>
    <p class="toolnote">${esc(t('weightNote'))}</p><div class="weights">${METRIC_KEYS.map(key=>`<label for="weight-${key}">${esc(t(key))}<input class="toolinput" id="weight-${key}" data-weight="${key}" type="number" min="0" max="100" step="1" value="${Math.round(weights[key]*100)}"></label>`).join('')}</div>
    <p class="toolnote" id="distanceNote">${esc(t('distanceNote'))}</p>${results.length?`<table class="tooltable" aria-describedby="distanceNote"><thead><tr><th>${esc(t('name'))}</th><th>${esc(t('distance'))}</th><th></th></tr></thead><tbody>${results.map(m=>`<tr><td><a href="${esc(charHref(m.d))}" data-tool-profile="${esc(m.d.slug)}">${esc(nameOf(m.d))}</a></td><td>${fmt(m.score,3)}${matchBreakdown(m)}</td><td><button class="btn" data-match-pair="${esc(m.d.slug)}" data-source="${esc(source.slug)}">${esc(t('comparePair'))}</button></td></tr>`).join('')}</tbody></table>`:`<p role="status">${esc(t('noMatches'))}</p>`}`;
}
function matchBreakdown(match){
  const parts=match.components;
  return `<details class="matchbreakdown"><summary>${esc(t('whyMatch'))}</summary><ul>${parts.map(c=>{
    const gap=state.matchBasis==='height'&&c.key!=='height'?c.difference:toDisp(c.difference);
    return `<li><span>${esc(t(c.key))}</span><span>${esc(fmt(gap)+valueSuffix(c.key,state.matchBasis))}</span><span class="distancepart">${fmt(c.contribution,3)}</span></li>`;
  }).join('')}</ul><p>${esc(t('contributionNote'))}</p></details>`;
}
function bindMatches(){
  bindFigurePicker('matchSource',[...DATA,...(state.sandbox?[sandboxRecord()]:[])],slug=>toolUpdate('matchSource',()=>{state.matchSource=slug;}));
  $('#matchBasis').onchange=e=>toolUpdate('matchBasis',()=>{state.matchBasis=e.target.value;});
  $('#resetWeights').onclick=()=>toolUpdate('resetWeights',()=>{state.matchWeights=null;});
  $$('[data-weight]').forEach(input=>input.onchange=()=>{
    if(!input.checkValidity()){input.reportValidity();return;}
    toolUpdate(input.id,()=>{state.matchWeights={...(state.matchWeights||Analysis.weights),[input.dataset.weight]:+input.value/100};});
  });
}

/* Numeric rounds use displayed precision; cup rounds always use the full UK rank. */
function newGameRound(){
  const key=state.gameMetric,basis=['height','cup'].includes(key)?'raw':state.gameBasis;
  const pool=DATA.filter(d=>key==='cup'?Analysis.cupSize(d.uk)&&Analysis.sizeParts(d[state.cupSystem]):shownValue(d,key,basis)!=null);
  if(pool.length<2){gameRound=null;return;}
  const a=Math.floor(Math.random()*pool.length),rest=pool.filter((_,i)=>i!==a),b=Math.floor(Math.random()*rest.length);
  gameRound={left:pool[a].slug,right:rest[b].slug,key,basis,unit:state.unit,answer:null};
}
function gameHTML(){
  const key=state.gameMetric,basis=['height','cup'].includes(key)?'raw':state.gameBasis;
  if(!gameRound||gameRound.key!==key||gameRound.basis!==basis||(key!=='cup'&&gameRound.unit!==state.unit))newGameRound();
  const round=gameRound,figures=round?[bySlug.get(round.left),bySlug.get(round.right)]:[];
  return `<div class="toolform"><label for="gameMetric">${esc(t('metric'))}<select id="gameMetric">${distributionOptions(key)}</select></label>${key!=='cup'?`<label for="gameBasis">${esc(t('basis'))}<select id="gameBasis"${key==='height'?' disabled':''}>${basisOptions(basis)}</select></label>`:''}<button class="btn" id="gameReset">${esc(t('gameReset'))}</button></div>
    <p class="toolnote">${esc(t(key==='cup'?'cupGameNote':'gameNote'))}</p><div class="toolstats"><span>${esc(t('gameScore'))}<strong>${gameScore.correct} / ${gameScore.total}</strong></span><span>${esc(t('streak'))}<strong>${gameScore.streak}</strong></span></div>
    ${!round?`<p>${esc(t('notEnough'))}</p>`:`<div class="gamepair">${figures.map((d,i)=>`<div class="gamefigure"><img src="${THUMB}/320/${d.official}.webp" width="90" height="140" alt=""><div><h3>${esc(nameOf(d))}</h3><div class="gamevalue">${i===0||round.answer?esc(key==='cup'?cupText(d):valueText(d,key,basis)):'?'}</div>${key==='cup'&&round.answer&&state.cupSystem!=='uk'?`<div class="gamebasis">UK ${esc(d.uk)}</div>`:''}</div></div>`).join('')}</div>
    <p class="gameresult" role="status">${round.answer?esc(t(round.correct?'correct':'incorrect')+' · '+t(round.outcome)):''}</p><div class="gameactions">${['higher','lower','equal'].map(k=>`<button class="btn" id="guess-${k}" data-guess="${k}"${round.answer?' disabled':''}>${esc(t(k))}</button>`).join('')}<button class="btn primary" id="nextRound"${!round.answer?' hidden disabled':''}>${esc(t('nextRound'))}</button></div>`}`;
}
function bindGame(){
  $('#gameMetric').onchange=e=>toolUpdate('gameMetric',()=>{state.gameMetric=e.target.value;gameRound=null;});
  if($('#gameBasis'))$('#gameBasis').onchange=e=>toolUpdate('gameBasis',()=>{state.gameBasis=e.target.value;gameRound=null;});
  $('#gameReset').onclick=()=>toolUpdate('gameReset',()=>{gameScore={correct:0,total:0,streak:0};gameRound=null;});
  $$('[data-guess]').forEach(b=>b.onclick=()=>{
    if(gameRound.answer)return;
    const left=bySlug.get(gameRound.left),right=bySlug.get(gameRound.right);
    const result=Analysis.gameOutcome(left,right,gameRound.key,gameRound.basis,state.unit);
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
