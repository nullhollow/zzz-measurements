/* Roster presentation state does not change measurements or ranking rules. */
const TABLE_KEYS=['name','height','bust','band','waist','hip','thigh','uk','whr','whtr','thr','thh','shape','bal','note'];
const DEFAULT_TABLE_COLUMNS=['height','bust','waist','hip','uk'];
function compareTableValues(a,b,direction,numeric,language){
  if(a==null)return b==null?0:1;
  if(b==null)return -1;
  return (numeric?a-b:String(a).localeCompare(String(b),language))*direction;
}
function parseTableSort(value){
  const [key,dir]=String(value||'').split(':');
  return TABLE_KEYS.includes(key)&&['1','-1'].includes(dir)?{k:key,dir:Number(dir)}:{k:'uk',dir:-1};
}
function parseTableColumns(value){
  if(!value)return null;
  const keys=[...new Set(value.split(','))].filter(k=>k!=='name'&&TABLE_KEYS.includes(k));
  return keys.length?keys:null;
}
function renderColumnPicker(all,chosen){
  const box=$('#columnOptions');
  box.innerHTML=all.filter(c=>c.k!=='name').map(c=>`<label><input type="checkbox" data-column="${c.k}" ${chosen.includes(c.k)?'checked':''}>${esc(c.t)}</label>`).join('')+`<button class="btn" id="restoreColumns">${esc(t('restoreColumns'))}</button>`;
  box.querySelectorAll('input').forEach(input=>input.onchange=()=>{
    const next=Array.from(box.querySelectorAll('input:checked'),e=>e.dataset.column);
    if(!next.length){input.checked=true;return;}
    tableColumns=next;renderTable(filtered());writeHash(false);
    box.querySelector(`[data-column="${input.dataset.column}"]`)?.focus();
  });
  $('#restoreColumns').onclick=()=>{tableColumns=null;renderTable(filtered());writeHash(false);$('#columnPicker summary').focus();};
}
function clearRosterFilters(){
  Object.assign(state,{q:'',cup:'all',height:'all',shape:'all',balance:'all',thighs:'all',rng:{}});
  syncControls();renderFilterPanel();render();
}
function renderActiveFilters(){
  const entries=[];
  if(state.q)entries.push({key:'q',text:state.q});
  const labels={cup:'bustTier',height:'heightClass',shape:'shape',balance:'build',thighs:'thighClass'};
  for(const [key,label] of Object.entries(labels))if(state[key]!=='all')entries.push({key,text:t(label)+': '+tagText(state[key])});
  for(const [key,range] of Object.entries(state.rng)){
    const metric=RANGES.find(m=>m.k===key);
    if(metric)entries.push({key:'rng:'+key,text:t(metric.lk)+': '+range.map(v=>fmt(isCm()?v:v/2.54)).join('–')+USUF()});
  }
  const box=$('#activeFilters');box.hidden=!entries.length||(TOOLS_PAGE&&state.view!=='distribution');
  box.innerHTML=entries.map(e=>`<button class="btn" data-remove-filter="${esc(e.key)}" aria-label="${esc(t('removeFilter')+': '+e.text)}">${esc(e.text)} ×</button>`).join('')+(entries.length?`<button class="btn" id="clearActive">${esc(t('clearFilters'))}</button>`:'');
  box.querySelectorAll('[data-remove-filter]').forEach(b=>b.onclick=()=>{
    const key=b.dataset.removeFilter;
    if(key.startsWith('rng:'))delete state.rng[key.slice(4)];else state[key]=key==='q'?'':'all';
    syncControls();renderFilterPanel();render();
    (box.querySelector('button')||$('#q')).focus();
  });
  if($('#clearActive'))$('#clearActive').onclick=()=>{clearRosterFilters();$('#q').focus();};
}
$('#clearEmpty').onclick=()=>{clearRosterFilters();$('#q').focus();};
let helpTrigger=null;
const helpDialog=document.createElement('dialog');
helpDialog.className='settings-dialog';helpDialog.id='measurementHelp';helpDialog.setAttribute('aria-labelledby','helpTitle');
document.body.append(helpDialog);
function closeMeasurementHelp(){helpDialog.close();if(!$('#overlay').classList.contains('open'))document.body.classList.remove('modal-open');helpTrigger?.focus();}
document.addEventListener('click',e=>{
  const button=e.target.closest('[data-help]');if(!button)return;
  helpTrigger=button;
  const key=button.dataset.help;
  const texts=key==='cup'?['helpCup']:key==='ratio'?['helpRatio']:['helpOverview','helpCup','helpRatio','helpMissing'];
  helpDialog.innerHTML=`<h2 id="helpTitle">${esc(t('measurementHelp'))}</h2>${texts.map(k=>`<p>${esc(t(k))}</p>`).join('')}<button class="btn" id="helpClose">${esc(t('close'))}</button>`;
  helpDialog.showModal();document.body.classList.add('modal-open');$('#helpClose').onclick=closeMeasurementHelp;$('#helpClose').focus();
});
helpDialog.addEventListener('cancel',e=>{e.preventDefault();closeMeasurementHelp();});
helpDialog.addEventListener('keydown',e=>{if(e.key==='Tab')trapDialogFocus(helpDialog,e);});
