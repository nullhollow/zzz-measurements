/* Pure exploration math. Keep in step with analysis_math.py. */
const Analysis = (() => {
  const fields = {bust:'bust_cm', waist:'waist_cm', hip:'hip_cm', thigh:'thigh_cm', height:'stature_cm', underbust:'band_cm'};
  const weights = {bust:.25, waist:.2, hip:.2, thigh:.15, height:.2, underbust:0};
  const cupBase={A:1,B:2,C:3,D:4,E:5,F:6,G:7,H:8,J:9,K:10,L:11,M:12,N:13};
  function sizeParts(size){
    const m=/^(\d+)\s*([A-Za-z]+)$/.exec(size||'');
    return m?{cup:m[2].toUpperCase(),band:Number(m[1])}:null;
  }
  function cupSize(size){
    const parts=sizeParts(size);
    if(!parts||!cupBase[parts.cup[0]])return null;
    return {...parts,score:cupBase[parts.cup[0]]*10000+(parts.cup.length===1?1000:0)+parts.band};
  }
  function cupDistribution(roster,system='uk'){
    if(!['uk','us','eu'].includes(system))system='uk';
    const groups=new Map();
    for(const d of roster){const s=system==='uk'?cupSize(d.uk):sizeParts(d[system]);if(s)groups.set(s.cup,(groups.get(s.cup)||0)+1);}
    const order=cup=>system==='uk'?cupSize('0'+cup).score:cup.charCodeAt(0)*1000+cup.length;
    const bins=[...groups].map(([cup,count])=>({cup,count})).sort((a,b)=>order(a.cup)-order(b.cup));
    const peak=Math.max(0,...groups.values());
    return {count:[...groups.values()].reduce((a,b)=>a+b,0),bins,modes:bins.filter(b=>b.count===peak).map(b=>b.cup)};
  }
  const percentage = (v,h) => v != null && h > 0 ? v / h * 100 : null;
  function value(d,key,basis='raw',target=160){
    const v = d[fields[key]];
    if(key === 'height' || basis === 'raw') return v ?? null;
    return v != null && d.stature_cm > 0 ? v / d.stature_cm * (basis === 'scaled' ? target : 100) : null;
  }
  const displayed = v => v == null ? null : Number(v.toFixed(1));
  const difference = (v,r) => v != null && r != null ? v-r : null;
  function outcome(left,right){
    const a=displayed(left), b=displayed(right);
    return a == null || b == null ? null : a === b ? 'equal' : b > a ? 'higher' : 'lower';
  }
  function gameOutcome(left,right,key,basis='raw',unit='cm'){
    const score=d=>{
      if(key==='cup')return cupSize(d.uk)?.score??null;
      const v=value(d,key,basis);
      return v!=null&&unit==='in'&&(basis!=='height'||key==='height')?v/2.54:v;
    };
    return outcome(score(left),score(right));
  }
  function matches(roster,source,chosen=weights,basis='raw'){
    const spans={};
    for(const key of Object.keys(fields)){
      const vs=roster.map(d=>value(d,key,basis)).filter(v=>v!=null);
      spans[key]=vs.length ? Math.max(...vs)-Math.min(...vs)||1 : 1;
    }
    return roster.filter(d=>d.slug!==source.slug).map(d=>{
      let score=0,total=0;
      for(const key of Object.keys(fields)){
        const w=chosen[key]||0, a=value(source,key,basis), b=value(d,key,basis);
        if(!Number.isFinite(w)||w<=0||a==null||b==null) continue;
        score+=w*Math.abs(a-b)/spans[key]; total+=w;
      }
      return {d,score:total ? score/total : null};
    }).filter(x=>x.score!=null).sort((a,b)=>a.score-b.score);
  }
  function distribution(values,count=10){
    const vs=values.filter(v=>v!=null&&Number.isFinite(v)).sort((a,b)=>a-b), n=vs.length;
    if(!n) return {count:0,median:null,bins:[]};
    const lo=vs[0],hi=vs[n-1],size=lo===hi?1:count,step=(hi-lo)/size;
    const bins=Array.from({length:size},(_,i)=>({lo:lo+i*step,hi:lo+(i+1)*step,count:0}));
    for(const v of vs) bins[step ? Math.min(size-1,Math.floor((v-lo)/step)) : 0].count++;
    return {count:n,median:(vs[Math.floor((n-1)/2)]+vs[Math.floor(n/2)])/2,bins};
  }
  return {fields,weights,sizeParts,cupSize,cupDistribution,percentage,value,displayed,difference,outcome,gameOutcome,matches,distribution};
})();
