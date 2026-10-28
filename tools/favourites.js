const FavouriteBoard = (() => {
  const math=typeof Analysis==='undefined'?require('./analysis.js'):Analysis;
  const tiers=['SSS','S','A','B','C','D','E'];
  const colours=['#F2A621','#FFD500','#AC61F2','#3686F5','#C4C8CE','#92969E','#50545C'];
  function empty(){return {v:1,title:'',author:'',numbering:'overall',includeSummary:false,tiers:tiers.map(()=>[])};}
  function parse(raw,slugs){
    if(!raw||raw.v!==1||!Array.isArray(raw.tiers)||raw.tiers.length!==tiers.length)return null;
    const valid=new Set(slugs),seen=new Set(),board=empty();
    board.title=typeof raw.title==='string'?raw.title.slice(0,80):'';
    board.author=typeof raw.author==='string'?raw.author.slice(0,40):'';
    board.numbering=raw.numbering==='tier'?'tier':'overall';
    board.includeSummary=raw.includeSummary===true;
    for(const [i,row] of raw.tiers.entries()){
      if(!Array.isArray(row))return null;
      board.tiers[i]=row.filter(slug=>valid.has(slug)&&!seen.has(slug)&&seen.add(slug));
    }
    return board;
  }
  function move(board,slug,tier,before){
    const next={...board,tiers:board.tiers.map(row=>row.filter(s=>s!==slug))};
    if(tier>=0){const row=next.tiers[tier],index=before?row.indexOf(before):-1;row.splice(index<0?row.length:index,0,slug);}
    return next;
  }
  function ranks(board){
    let n=0;return board.tiers.map(row=>row.map((slug,i)=>({slug,rank:board.numbering==='tier'?i+1:++n})));
  }
  function wrapText(text,measure,width,maxLines,hyphenate=false,wordWrap=false){
    const chars=Array.from(text),lines=[];
    const latin=ch=>/[A-Za-z]/.test(ch||'');
    let start=0;
    while(start<chars.length&&lines.length<maxLines){
      let end=start;
      while(end<chars.length&&measure(chars.slice(start,end+1).join(''))<=width)end++;
      if(end===start)end++;
      if(end<chars.length&&lines.length===maxLines-1){
        while(end>start&&measure(chars.slice(start,end).join('')+'…')>width)end--;
        lines.push(chars.slice(start,end).join('').trimEnd()+'…');break;
      }
      let suffix='';
      if(wordWrap&&end<chars.length&&latin(chars[end-1])&&latin(chars[end])){
        const space=chars.slice(start,end).lastIndexOf(' ');if(space>0)end=start+space;
      }
      if(hyphenate&&end<chars.length&&latin(chars[end-1])&&latin(chars[end])){
        while(end>start+1&&measure(chars.slice(start,end).join('')+'-')>width)end--;
        if(latin(chars[end-1])&&latin(chars[end]))suffix='-';
      }
      lines.push(chars.slice(start,end).join('').trimEnd()+suffix);start=end;
      while(chars[start]===' ')start++;
    }
    return lines;
  }
  function summary(board,roster,system='uk'){
    const bySlug=new Map(roster.map(d=>[d.slug,d]));
    const selected=board.tiers.flat().slice(0,10).map(slug=>bySlug.get(slug));
    const metrics=[['bust','bust_cm'],['waist','waist_cm'],['hips','hip_cm'],['thighs','thigh_cm'],['height','stature_cm']]
      .map(([field,key])=>({field,...math.numericSummary(selected.map(d=>d[key]))}));
    const groups=['height','bust','waist','hips','thighs','shape','balance'].map(field=>{
      const known=selected.filter(d=>d.tags[field]&&!['n/a','?'].includes(d.tags[field]));
      const counts=new Map();known.forEach(d=>counts.set(d.tags[field],(counts.get(d.tags[field])||0)+1));
      const categories=[...new Set(roster.map(d=>d.tags[field]).filter(tag=>tag&&!['n/a','?'].includes(tag)))].map(tag=>({tag,count:counts.get(tag)||0}));
      return {field,count:known.length,categories};
    });
    return {count:selected.length,system,cups:math.cupLabelSummary(selected,system),thighPins:selected.filter(d=>d.thigh_pin).length,metrics,groups};
  }

  return {tiers,colours,empty,parse,move,ranks,wrapText,summary};
})();
if(typeof module!=='undefined')module.exports=FavouriteBoard;

if(typeof document!=='undefined')(() => {
  const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
  const data=FAVOURITES_DATA,bySlug=new Map(data.map(d=>[d.slug,d])),slugs=data.map(d=>d.slug);
  const DRAFT='zzz-favourites-v1',SAVED='zzz-favourite-boards-v1';
  let lang='en',cupSystem='uk',board=FavouriteBoard.empty(),selected='',undo=[],dragged='',previewUrl='';
  let savedBoards=[];
  const t=(key,values={})=>Object.entries(values).reduce((s,[k,v])=>s.replaceAll('{'+k+'}',v),FAVOURITES_I18N[lang][key]);
  const name=d=>lang==='en'?d.display:d['name_'+lang]||d.display;
  const status=text=>$('#favStatus').textContent=text;
  function store(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch(_){status(t('favStorageError'));return false;}}
  function snapshot(){undo.push({board:structuredClone(board),saved:structuredClone(savedBoards)});if(undo.length>50)undo.shift();}
  function params(){const p=new URLSearchParams(location.hash.slice(1));p.set('lang',lang);p.set('th',siteTheme.preference);p.set('cups',cupSystem);return p;}
  function syncLinks(){
    const p=params();p.delete('board');
    $('#measurementsLink').href='index.html#'+p;
    $('#toolsLink').href='tools.html#'+p;
    $('#methodologyLink').href=(lang==='en'?'':lang+'/')+'methodology.html';
  }
  function commit(){
    render();store(DRAFT,board);
    const p=params();if(p.has('board'))p.set('board',JSON.stringify(board));
    history.replaceState(null,'','#'+p);syncLinks();
  }
  function move(slug,tier,before){
    if(before===slug)return;
    snapshot();board=FavouriteBoard.move(board,slug,tier,before);selected=slug;commit();
    status(t('favMoved',{name:name(bySlug.get(slug)),tier:tier<0?t('favUnranked'):FavouriteBoard.tiers[tier]}));
  }
  function tile(d,rank){
    const button=document.createElement('button');button.type='button';button.className='fav-agent';button.dataset.slug=d.slug;button.draggable=true;
    button.setAttribute('aria-pressed',String(selected===d.slug));button.setAttribute('aria-label',name(d)+(rank?' #'+rank:''));
    const picture=document.createElement('picture'),source=document.createElement('source'),img=document.createElement('img');
    source.type='image/avif';source.srcset=`character_images/thumbs/avif/320/${d.official}.avif`;
    img.src=`character_images/thumbs/320/${d.official}.webp`;img.alt='';img.loading='lazy';img.draggable=false;
    picture.append(source,img);button.append(picture);
    if(rank){const badge=document.createElement('span');badge.className='fav-number';badge.textContent='#'+rank;button.append(badge);}
    const label=document.createElement('span');label.className='fav-agent-name';label.textContent=name(d);button.append(label);
    button.onclick=()=>{selected=selected===d.slug?'':d.slug;render();};
    button.ondragstart=e=>{dragged=d.slug;e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',d.slug);button.classList.add('dragging');};
    button.ondragend=()=>{dragged='';$$('.dragging,.drop-target,.insert-before').forEach(el=>el.classList.remove('dragging','drop-target','insert-before'));};
    return button;
  }
  function dropZone(el,tier){
    el.ondragover=e=>{
      if(!dragged)return;e.preventDefault();e.dataTransfer.dropEffect='move';
      $$('.drop-target,.insert-before').forEach(x=>x.classList.remove('drop-target','insert-before'));
      const target=e.target.closest('.fav-agent');if(target&&target.dataset.slug!==dragged)target.classList.add('insert-before');else el.classList.add('drop-target');
    };
    el.ondragleave=e=>{if(!el.contains(e.relatedTarget))$$('.drop-target,.insert-before').forEach(x=>x.classList.remove('drop-target','insert-before'));};
    el.ondrop=e=>{if(!dragged)return;e.preventDefault();const target=e.target.closest('.fav-agent');move(dragged,tier,target?.dataset.slug);dragged='';};
  }
  function render(){
    const active=document.activeElement,focusSlug=active?.dataset.slug,focusId=active?.id;
    $('#favTitle').value=board.title;$('#favTitle').placeholder=t('favDefaultTitle');$('#favAuthor').value=board.author;$('#favNumbering').value=board.numbering;
    const ranked=FavouriteBoard.ranks(board),container=$('#favBoard');container.replaceChildren();
    ranked.forEach((row,i)=>{
      const tier=document.createElement('section');tier.className='fav-tier';tier.dataset.tier=FavouriteBoard.tiers[i];tier.style.setProperty('--tier-fill',FavouriteBoard.colours[i]);if(i===6)tier.style.setProperty('--tier-ink','#FFFFFF');
      const label=document.createElement('button');label.type='button';label.className='fav-tier-label';label.textContent=FavouriteBoard.tiers[i];label.disabled=!selected;label.onclick=()=>move(selected,i);
      const members=document.createElement('div');members.className='fav-members';
      row.forEach(({slug,rank})=>members.append(tile(bySlug.get(slug),rank)));
      if(!row.length){const empty=document.createElement('span');empty.className='fav-empty';empty.textContent=t('favEmpty');members.append(empty);}
      tier.append(label,members);dropZone(tier,i);container.append(tier);
    });
    const placed=new Set(board.tiers.flat()),q=$('#favSearch').value.trim().toLowerCase();
    const pool=data.filter(d=>!placed.has(d.slug)),visible=pool.filter(d=>[d.display,d.name_ja,d.name_zh,d.slug].some(s=>s?.toLowerCase().includes(q))).sort((a,b)=>name(a).localeCompare(name(b),lang));
    const poolEl=$('#favPoolItems');poolEl.replaceChildren();visible.forEach(d=>poolEl.append(tile(d)));
    if(!visible.length){const empty=document.createElement('p');empty.className='fav-empty';empty.textContent=t('favNoResults');poolEl.append(empty);}
    $('#favPoolCount').textContent=pool.length;$('#favCount').textContent=t('favCount',{n:placed.size,total:data.length});
    $('#favSelected').textContent=selected?name(bySlug.get(selected)):t('favSelect');
    const index=board.tiers.findIndex(row=>row.includes(selected)),position=index<0?-1:board.tiers[index].indexOf(selected);
    $('#favTier').disabled=!selected;$('#favTier').value=index<0?'pool':String(index);
    $('#favEarlier').disabled=position<=0;$('#favLater').disabled=index<0||position===board.tiers[index].length-1;
    $('#favUndo').disabled=!undo.length;$('#favReset').disabled=!placed.size&&!board.title&&!board.author;$('#favExport').disabled=!placed.size;
    const previous=$('#favSaved').value;$('#favSaved').replaceChildren(new Option(t('favNone'),''));
    savedBoards.forEach((b,i)=>$('#favSaved').add(new Option(b.title||t('favDefaultTitle'),String(i))));$('#favSaved').value=previous;
    syncSavedButtons();
    renderSummary();
    if(focusSlug)$$('.fav-agent').find(el=>el.dataset.slug===focusSlug)?.focus({preventScroll:true});
    else if(focusId)document.getElementById(focusId)?.focus({preventScroll:true});
  }
  function applyLanguage(){
    document.documentElement.lang=lang;document.title=t('favHeading')+' · ZZZ Measurements';
    $$('[data-i18n]').forEach(el=>el.textContent=t(el.dataset.i18n));
    $$('[data-placeholder]').forEach(el=>el.placeholder=t(el.dataset.placeholder));
    $('#favSearch').setAttribute('aria-label',t('favSearch'));$('#lang').value=lang;$('#theme').value=siteTheme.preference;
    $('#favCupSystem').setAttribute('aria-label',t('favCupSystem'));
    $('#favTier').replaceChildren(...FavouriteBoard.tiers.map((label,i)=>new Option(label,String(i))),new Option(t('favUnranked'),'pool'));
    render();syncLinks();
  }
  function syncSavedButtons(){const disabled=$('#favSaved').value==='';$('#favLoad').disabled=disabled;$('#favDelete').disabled=disabled;}
  function tagLabel(field,tag){const record=data.find(d=>d.tags[field]===tag);return lang==='en'?tag:record['tags_'+lang][field];}
  const number=value=>value==null?'—':new Intl.NumberFormat(lang,{minimumFractionDigits:1,maximumFractionDigits:1}).format(value);
  function summaryDisplay(result){
    const cups=result.cups;
    const mode=cups.count?`${cups.modes.map(cup=>(cups.bins.find(b=>b.cup===cup).estimated?'≈':'')+cup).join(' / ')} · ${cups.modeCount}/${cups.count}`:'—';
    return {
      metrics:result.metrics.map(metric=>({...metric,label:(metric.field==='height'?'↕ ':'↔ ')+t('favMeasure_'+metric.field),value:number(metric.median)})),
      cups:[{label:t('favCommonCup')+' · '+result.system.toUpperCase(),value:mode},
        {label:t('favMeanCup')+' · '+result.system.toUpperCase(),value:cups.meanLabel?'≈'+cups.meanLabel:'—'}]
    };
  }
  function tableRow(label,values){
    const row=document.createElement('tr'),heading=document.createElement('th');heading.scope='row';heading.textContent=label;row.append(heading);
    const cells=values.map(value=>{const cell=document.createElement('td');cell.textContent=value;row.append(cell);return cell;});return {row,cells};
  }
  function renderSummary(){
    const result=FavouriteBoard.summary(board,data,cupSystem),display=summaryDisplay(result);
    $('#favSummary').hidden=!result.count;$('#favCupSystem').value=cupSystem;
    $('#favSummaryCount').textContent=t('favTopCount',{n:result.count});
    $('#favIncludeSummary').checked=board.includeSummary;
    $('#favPreferenceRows').replaceChildren(...display.metrics.map(metric=>{
      const {row,cells}=tableRow(metric.label,[metric.value]);row.dataset.field=metric.field;
      if(metric.count<result.count){const note=document.createElement('small');note.textContent=t('favMeasured',{n:metric.count,total:result.count});cells[0].append(note);}return row;
    }));
    $('#favCupRows').replaceChildren(...display.cups.map(cup=>tableRow(cup.label,[cup.value]).row));
    const range=stats=>stats.count?t('favRange',{low:number(stats.q1),high:number(stats.q3),n:stats.count}):'—';
    $('#favSummaryRanges').replaceChildren(...display.metrics.map(metric=>tableRow(t('favMeasure_'+metric.field),[range(metric)]).row));
    $('#favSummaryBreakdown').replaceChildren(...result.groups.map(group=>tableRow(t('favSummary_'+group.field),[group.count?group.categories.map(c=>`${tagLabel(group.field,c.tag)} ${c.count}/${group.count}`).join(' · '):'—']).row));
    $('#favSummaryPins').textContent=t('favTopPins',{n:result.thighPins});
    $('#favCupNotes').textContent=t('favTopCupCounts',{n:result.cups.count,total:result.count})+' '+t('favCupMethod')+(result.cups.estimatedCount?' '+t('favTopEstimates',{n:result.cups.estimatedCount}):'');
  }
  function boot(){
    const p=new URLSearchParams(location.hash.slice(1));let invalid=false;
    try{lang=localStorage.getItem('zzz-lang')||'en';board=FavouriteBoard.parse(JSON.parse(localStorage.getItem(DRAFT)),slugs)||FavouriteBoard.empty();const raw=JSON.parse(localStorage.getItem(SAVED));if(Array.isArray(raw))savedBoards=raw.map(b=>FavouriteBoard.parse(b,slugs)).filter(Boolean);}catch(_){}
    try{const saved=localStorage.getItem('zzz-cup-system');if(['uk','us','eu'].includes(saved))cupSystem=saved;}catch(_){}
    if(['uk','us','eu'].includes(p.get('cups')))cupSystem=p.get('cups');
    if(FAVOURITES_I18N[p.get('lang')])lang=p.get('lang');if(!FAVOURITES_I18N[lang])lang='en';
    if(p.has('board')){try{const shared=FavouriteBoard.parse(JSON.parse(p.get('board')),slugs);if(shared)board=shared;else invalid=true;}catch(_){invalid=true;}}
    if(['system','dark','light'].includes(p.get('th')))siteTheme.set(p.get('th'));
    selected='';undo=[];applyLanguage();if(invalid)status(t('favInvalid'));
  }
  $('#favTier').onchange=e=>{if(selected)move(selected,e.target.value==='pool'?-1:Number(e.target.value));};
  $('#favUnrank').onclick=()=>{if(selected)move(selected,-1);};dropZone($('#favPool'),-1);
  $('#favSearch').oninput=render;
  $('#favEarlier').onclick=()=>{const i=board.tiers.findIndex(row=>row.includes(selected)),row=board.tiers[i];move(selected,i,row[row.indexOf(selected)-1]);};
  $('#favLater').onclick=()=>{const i=board.tiers.findIndex(row=>row.includes(selected)),row=board.tiers[i],next=row[row.indexOf(selected)+2];move(selected,i,next);};
  for(const [id,key] of [['favTitle','title'],['favAuthor','author']]){
    let editing=false;
    $('#'+id).onfocus=()=>{editing=false;};
    $('#'+id).oninput=e=>{if(!editing){snapshot();editing=true;}board={...board,[key]:e.target.value};commit();};
  }
  $('#favNumbering').onchange=e=>{snapshot();board={...board,numbering:e.target.value};commit();};
  $('#favIncludeSummary').onchange=e=>{snapshot();board={...board,includeSummary:e.target.checked};commit();};
  $('#favCupSystem').onchange=e=>{cupSystem=e.target.value;try{localStorage.setItem('zzz-cup-system',cupSystem);}catch(_){}renderSummary();history.replaceState(null,'','#'+params());syncLinks();};
  $('#favUndo').onclick=()=>{const prior=undo.pop();if(!prior)return;board=prior.board;savedBoards=prior.saved;store(SAVED,savedBoards);commit();status('');};
  $('#favReset').onclick=()=>{snapshot();board=FavouriteBoard.empty();selected='';commit();status('');};
  $('#lang').onchange=e=>{lang=e.target.value;try{localStorage.setItem('zzz-lang',lang);}catch(_){}applyLanguage();const p=params();history.replaceState(null,'','#'+p);};
  $('#theme').onchange=e=>{siteTheme.set(e.target.value);const p=params();history.replaceState(null,'','#'+p);syncLinks();};
  $('#favShare').onclick=async()=>{
    const p=params();p.set('board',JSON.stringify(board));const url=new URL(location.href);url.hash=p.toString();
    try{await navigator.clipboard.writeText(url.href);status(t('favCopied'));}catch(_){window.prompt(t('favCopyFallback'),url.href);}
  };
  $('#favSaved').onchange=syncSavedButtons;
  $('#favSave').onclick=()=>{snapshot();const saved={...structuredClone(board),title:board.title.trim()||t('favDefaultTitle')},i=savedBoards.findIndex(b=>b.title===saved.title);if(i<0)savedBoards.push(saved);else savedBoards[i]=saved;if(store(SAVED,savedBoards)){render();status(t('favSavedStatus'));}};
  $('#favLoad').onclick=()=>{const chosen=savedBoards[Number($('#favSaved').value)];if(chosen){snapshot();board=structuredClone(chosen);selected='';commit();}};
  $('#favDelete').onclick=()=>{snapshot();savedBoards.splice(Number($('#favSaved').value),1);if(store(SAVED,savedBoards)){render();status(t('favDeleted'));}};
  $('#favPreviewClose').onclick=()=>$('#favPreview').close();
  $('#favExport').onclick=async()=>{
    const button=$('#favExport');button.disabled=true;status(t('favExporting'));
    try{
      const canvas=await exportImage(),blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('JPG export failed')),'image/jpeg',0.9));
      if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=URL.createObjectURL(blob);
      $('#favPreviewImage').src=previewUrl;$('#favDownload').href=previewUrl;$('#favPreview').showModal();status('');
    }catch(error){status(t('favExportError'));}finally{button.disabled=!board.tiers.flat().length;}
  };
  async function exportImage(){
    const exportBoard=structuredClone(board),rows=FavouriteBoard.ranks(exportBoard),names=exportBoard.tiers.flat().map(s=>name(bySlug.get(s)));
    const result=FavouriteBoard.summary(exportBoard,data,cupSystem),displayRows=summaryDisplay(result);
    const style=getComputedStyle(document.body),display=style.getPropertyValue('--disp'),body=style.getPropertyValue('--body');
    await Promise.all([document.fonts.load(`22px ${body}`,names.join('')+JSON.stringify(displayRows)+t('favCupApproxNote')),document.fonts.load(`40px ${display}`,(exportBoard.title||t('favDefaultTitle'))+t('favPreferences'))]);await document.fonts.ready;
    const images=new Map(await Promise.all(exportBoard.tiers.flat().map(async slug=>{
      const img=new Image();img.src=`character_images/${bySlug.get(slug).official}.webp`;await img.decode();return [slug,img];
    })));
    const rowHeight=row=>Math.ceil(row.length/6)*216+24;
    const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=`22px ${body}`;
    const summaryHeight=exportBoard.includeSummary?432:0;
    const width=1080,height=220+rows.filter(row=>row.length).reduce((h,row)=>h+rowHeight(row),0)+summaryHeight,scale=2;
    canvas.width=width*scale;canvas.height=height*scale;
    const colour=key=>style.getPropertyValue('--'+key).trim();
    ctx.scale(scale,scale);ctx.imageSmoothingQuality='high';
    ctx.fillStyle=colour('ink');ctx.fillRect(0,0,width,height);
    ctx.fillStyle=colour('concrete');ctx.font=`40px ${display}`;
    drawText(ctx,exportBoard.title||t('favDefaultTitle'),40,65,1000,46,2);
    ctx.font=`18px ${body}`;ctx.fillStyle=colour('dim');ctx.fillText('ZENLESS ZONE ZERO'+(exportBoard.author?' · '+exportBoard.author:''),40,145);
    let y=172;
    rows.forEach((row,i)=>{
      if(!row.length)return;const height=rowHeight(row);
      ctx.fillStyle=FavouriteBoard.colours[i];ctx.fillRect(40,y,88,height-2);
      ctx.fillStyle=i===6?'#FFFFFF':'#17171C';ctx.font=`${i===0?24:36}px ${display}`;ctx.textAlign='center';ctx.fillText(FavouriteBoard.tiers[i],84,y+height/2+12);ctx.textAlign='left';
      row.forEach(({slug,rank},j)=>{
        const x=148+(j%6)*146,top=y+14+Math.floor(j/6)*216,img=images.get(slug),scale=Math.max(130/img.naturalWidth,140/img.naturalHeight);
        ctx.fillStyle=colour('panel');ctx.fillRect(x,top,130,140);
        ctx.save();ctx.beginPath();ctx.rect(x,top,130,140);ctx.clip();ctx.drawImage(img,x+(130-img.naturalWidth*scale)/2,top,img.naturalWidth*scale,img.naturalHeight*scale);ctx.restore();
        ctx.font='bold 19px '+body;const badge=ctx.measureText('#'+rank).width+14;
        ctx.fillStyle=FavouriteBoard.colours[i];ctx.fillRect(x,top,badge,28);ctx.fillStyle=i===6?'#FFFFFF':'#17171C';ctx.fillText('#'+rank,x+7,top+21);
        ctx.fillStyle=colour('concrete');ctx.font=`19px ${body}`;drawText(ctx,name(bySlug.get(slug)),x,top+163,130,22,3,lang==='en');
      });
      ctx.fillStyle=colour('line2');ctx.fillRect(128,y+height-2,912,1);y+=height;
    });
    if(exportBoard.includeSummary){
      const start=y;ctx.fillStyle=colour('concrete');ctx.font=`30px ${display}`;ctx.fillText(t('favPreferences'),40,start+38);
      ctx.font=`20px ${body}`;ctx.fillStyle=colour('dim');ctx.fillText(t('favMetric'),40,start+68);ctx.fillStyle=colour('concrete');ctx.fillText(t('favTopCount',{n:result.count}),650,start+68);
      displayRows.metrics.forEach((metric,i)=>{
        const top=start+105+i*44;ctx.font=`22px ${body}`;ctx.fillStyle=colour({bust:'bust',waist:'waist',hips:'hips',thighs:'thighs',height:'brass'}[metric.field]);ctx.fillText(metric.label,40,top);ctx.fillStyle=colour('concrete');ctx.fillText(metric.value,650,top);
        if(metric.count<result.count){ctx.font=`16px ${body}`;ctx.fillStyle=colour('dim');ctx.fillText(t('favMeasured',{n:metric.count,total:result.count}),650,top+20);}
      });
      displayRows.cups.forEach((cup,i)=>{const top=start+325+i*44;ctx.fillStyle=colour('concrete');ctx.font=`20px ${body}`;ctx.fillText(cup.label,40,top);ctx.font=`18px ${body}`;drawText(ctx,cup.value,650,top,390,20,2);});
      ctx.fillStyle=colour('dim');ctx.font=`16px ${body}`;drawText(ctx,t('favCupApproxNote'),40,start+405,1000,18,2);
    }
    ctx.fillStyle=colour('dim');ctx.font=`15px ${body}`;ctx.fillText('ZZZ Measurements · Art © HoYoverse',40,height-18);
    return canvas;
  }
  function drawText(ctx,text,x,y,width,lineHeight,maxLines,hyphenate=false){
    FavouriteBoard.wrapText(text,s=>ctx.measureText(s).width,width,maxLines,hyphenate)
      .forEach((line,i)=>ctx.fillText(line,x,y+i*lineHeight));
  }
  window.addEventListener('hashchange',boot);boot();
  if('serviceWorker' in navigator&&location.protocol.startsWith('http'))navigator.serviceWorker.register('sw.js').catch(()=>{});
})();
