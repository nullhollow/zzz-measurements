/* Shared by static profiles and the interactive chart. Originals load on demand. */
window.ArtworkViewer=(()=>{
  const dialog=document.createElement('dialog');dialog.className='art-viewer';dialog.setAttribute('aria-labelledby','artTitle');dialog.id='artViewer';document.body.append(dialog);
  let items=[],copy={},index=0,zoom=1,fitted=true,trigger=null,pointers=new Map(),pinch=null,pan=null,bodyLocked=false;
  const find=s=>dialog.querySelector(s);
  function size(){const img=find('img'),box=find('.art-viewport');if(!img||!box)return;const a=items[index];if(fitted)zoom=Math.min((box.clientWidth-32)/a.width,(box.clientHeight-32)/a.height);img.style.width=Math.max(1,a.width*zoom)+'px';find('#artZoom').value=Math.round(zoom*100);}
  function setZoom(value){const box=find('.art-viewport'),old=zoom;fitted=false;zoom=Math.max(.01,Math.min(3,value));const x=(box.scrollLeft+box.clientWidth/2)*zoom/old-box.clientWidth/2,y=(box.scrollTop+box.clientHeight/2)*zoom/old-box.clientHeight/2;size();box.scrollTo(x,y);}
  function show(next){
    index=(next+items.length)%items.length;zoom=1;fitted=true;pointers.clear();pinch=pan=null;
    const a=items[index];find('#artChoice').value=index;find('#artStatus').textContent=copy.loadingArt;find('#artRetry').hidden=true;
    find('#artMeta').textContent=`${a.width} × ${a.height} px · PNG · ${(a.bytes/1048576).toFixed(1)} MB`;
    find('#artDownload').href=a.file;find('#artDownload').download=a.file.split('/').pop();find('#artSource').href=a.source;
    const img=find('img');img.alt=a.label;img.onload=()=>{find('#artStatus').textContent='';size();};img.onerror=()=>{find('#artStatus').textContent=copy.failedArt;find('#artRetry').hidden=false;};img.src=a.file;size();find('.art-viewport').scrollTo(0,0);
  }
  function close(){if(!dialog.open)return;dialog.close();if(!bodyLocked)document.body.classList.remove('modal-open');trigger?.focus();}
  function open(rows,strings,at=0,from=document.activeElement){
    if(!rows.length)return;items=rows;copy=strings;trigger=from;bodyLocked=document.body.classList.contains('modal-open');document.body.classList.add('modal-open');
    const el=(tag,text,cls)=>{const node=document.createElement(tag);node.textContent=text;if(cls)node.className=cls;return node;};
    dialog.replaceChildren();const head=el('div','','art-toolbar'),title=el('h2',copy.originalViewer);title.id='artTitle';head.append(title);
    const select=el('select','');select.id='artChoice';select.setAttribute('aria-label',copy.originalViewer);items.forEach((a,i)=>{const o=el('option',a.label);o.value=i;select.append(o);});select.onchange=()=>show(Number(select.value));head.append(select);
    for(const [label,fn] of [[copy.previousArt,()=>show(index-1)],[copy.nextArt,()=>show(index+1)]]){const b=el('button',label,'btn');b.disabled=items.length<2;b.onclick=fn;head.append(b);}
    const zlabel=el('label',copy.zoomArt),range=el('input','');range.id='artZoom';range.type='range';range.min=1;range.max=300;range.step=1;range.value=100;range.oninput=()=>setZoom(Number(range.value)/100);zlabel.append(range);head.append(zlabel);
    const fit=el('button',copy.fitArt,'btn');fit.onclick=()=>{fitted=true;size();find('.art-viewport').scrollTo(0,0);};head.append(fit);const actual=el('button','100%','btn');actual.onclick=()=>setZoom(1);head.append(actual);
    const bgLabel=el('label',copy.backgroundArt),bg=el('select','');['neutral','light','dark'].forEach(k=>{const o=el('option',copy[k==='neutral'?'neutralArt':k]);o.value=k;bg.append(o);});bg.onchange=()=>dialog.dataset.background=bg.value;bgLabel.append(bg);head.append(bgLabel);dialog.dataset.background='neutral';
    const exit=el('button',copy.close,'btn');exit.onclick=close;exit.id='artClose';head.append(exit);dialog.append(head);
    const viewport=el('div','','art-viewport');viewport.tabIndex=0;viewport.setAttribute('aria-label',copy.originalViewer);const img=el('img','');img.draggable=false;viewport.append(img);dialog.append(viewport);
    const footer=el('div','','art-footer'),status=el('span','');status.id='artStatus';status.setAttribute('role','status');const meta=el('span','');meta.id='artMeta';footer.append(status,meta);
    for(const [id,label] of [['artDownload',copy.downloadOriginal],['artSource',copy.sourceOriginal]]){const a=el('a',label);a.id=id;if(id==='artSource'){a.target='_blank';a.rel='noopener';}footer.append(a);}
    const retry=el('button',copy.retryArt,'btn');retry.id='artRetry';retry.hidden=true;retry.onclick=()=>show(index);footer.append(retry,el('small',copy.artCredit));dialog.append(footer);
    viewport.onpointerdown=e=>{if(e.button!==0)return;viewport.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});pan={x:e.clientX,y:e.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};if(pointers.size===2){const [a,b]=[...pointers.values()];pinch={distance:Math.hypot(a.x-b.x,a.y-b.y),zoom};}};
    viewport.onpointermove=e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2&&pinch){const [a,b]=[...pointers.values()];setZoom(pinch.zoom*Math.hypot(a.x-b.x,a.y-b.y)/Math.max(1,pinch.distance));}else if(pan){viewport.scrollLeft=pan.left+pan.x-e.clientX;viewport.scrollTop=pan.top+pan.y-e.clientY;}};
    const release=e=>{pointers.delete(e.pointerId);pinch=pan=null;};viewport.onpointerup=release;viewport.onpointercancel=release;
    dialog.showModal();show(at);exit.focus();
  }
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
  dialog.addEventListener('keydown',e=>{if(e.key==='Tab'){const buttons=[...dialog.querySelectorAll('button,select,input,a[href],[tabindex="0"]')].filter(b=>!b.disabled&&!b.hidden&&b.offsetParent!==null),first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}if(!['INPUT','SELECT'].includes(e.target.tagName)&&fitted&&['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();show(index+(e.key==='ArrowLeft'?-1:1));}});
  window.addEventListener('resize',()=>{if(dialog.open)size();});
  document.addEventListener('click',e=>{const a=e.target.closest('[data-art-index]'),config=document.querySelector('#artworkConfig');if(a&&config){e.preventDefault();const c=JSON.parse(config.textContent);open(c.items,c.copy,Number(a.dataset.artIndex),a);}});
  return {open,close};
})();
