/* Global display preferences. Source values and UK ranking stay independent. */
function cupSystemName(){ return state.cupSystem.toUpperCase(); }
function displayCup(d){ return d[state.cupSystem]||'—'; }
function cupText(d){ return `${cupSystemName()} ${displayCup(d)}`; }
function displayCupLetter(d){ return Analysis.sizeParts(d[state.cupSystem])?.cup||'—'; }
function cupSizeLabel(){ return `${t('cupSize')} (${cupSystemName()})`; }
function syncMeasurementSettings(){
  $('#uCm').setAttribute('aria-pressed',state.unit==='cm');
  $('#uIn').setAttribute('aria-pressed',state.unit==='in');
  $$('#cupSystemToggle button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.cupSystem===state.cupSystem));
  $('#settingsBtn').title=`${state.unit.toUpperCase()} · ${cupSystemName()}`;
  $('#settingsClose').setAttribute('aria-label',t('close'));
}
function refreshMeasurements(){
  const focused=document.activeElement;
  renderFilterPanel();render();syncMeasurementSettings();
  if($('#overlay').classList.contains('open')){
    if(mctx.slug)openModal(mctx.slug,mctx);else if($('#modal .cmptable'))openCompare();
  }
  if($('#settingsDialog').open&&focused?.isConnected)focused.focus();
}
function setUnit(unit){
  state.unit=unit==='in'?'in':'cm';
  try{localStorage.setItem('zzz-unit',state.unit);}catch(_){}
  refreshMeasurements();
}
function setCupSystem(system){
  if(!['uk','us','eu'].includes(system))return;
  state.cupSystem=system;
  state.distSelection='';
  try{localStorage.setItem('zzz-cup-system',system);}catch(_){}
  refreshMeasurements();
}
function trapDialogFocus(dialog,event){
  if(event.key!=='Tab')return;
  const buttons=[...dialog.querySelectorAll('button,input,select,a[href]')].filter(b=>!b.disabled&&b.offsetParent!==null),first=buttons[0],last=buttons[buttons.length-1];
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
}
function trapSettingsFocus(event){trapDialogFocus($('#settingsDialog'),event);}
let settingsTrigger=null,settingsTriggerId='';
function openSettings(){
  if($('#settingsDialog').open)return;
  settingsTrigger=document.activeElement;settingsTriggerId=settingsTrigger?.id||'';
  syncMeasurementSettings();$('#settingsDialog').showModal();document.body.classList.add('modal-open');
  (state.unit==='in'?$('#uIn'):$('#uCm')).focus();
}
function closeSettings(){
  if(!$('#settingsDialog').open)return;
  $('#settingsDialog').close();
  if(!$('#overlay').classList.contains('open'))document.body.classList.remove('modal-open');
  const trigger=settingsTrigger?.isConnected?settingsTrigger:document.getElementById(settingsTriggerId);
  (trigger||$('#settingsBtn')).focus();
}
$('#settingsDialog').addEventListener('cancel',e=>{e.preventDefault();closeSettings();});
$('#settingsDialog').addEventListener('click',e=>{
  if(e.target!==$('#settingsDialog'))return;
  const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeSettings();
});
document.addEventListener('click',e=>{if(e.target.closest('[data-open-settings]'))openSettings();});
$('#uCm').onclick=()=>setUnit('cm');$('#uIn').onclick=()=>setUnit('in');
$$('#cupSystemToggle button').forEach(b=>b.onclick=()=>setCupSystem(b.dataset.cupSystem));
$('#settingsClose').onclick=closeSettings;$('#settingsDone').onclick=closeSettings;
