/* Shared UK cup ordering and exploration math. Keep in step with analysis_math.py. */
const Analysis = (() => {
  const fields = {bust:'bust_cm', waist:'waist_cm', hip:'hip_cm', thigh:'thigh_cm', height:'stature_cm', underbust:'band_cm'};
  const weights = {bust:.25, waist:.2, hip:.2, thigh:.15, height:.2, underbust:0};
  const ukCups='AA A B C D DD E F FF G GG H HH J JJ K KK L LL M MM N NN'.split(' ');
  const cupOrders={uk:ukCups,us:'AA A B C D DD DDD DDDD H I J K L M N O P Q R S T U V'.split(' '),eu:'AA A B C D E F G H I J K L M N O P Q R S T U V'.split(' ')};
  function sizeParts(size){
    const m=/^≈?(\d+)\s*([A-Za-z]+)$/.exec(size||'');
    return m?{cup:m[2].toUpperCase(),band:Number(m[1])}:null;
  }
  function cupSize(size){
    if(String(size||'').startsWith('≈'))return null;
    const parts=sizeParts(size);
    const rank=parts?ukCups.indexOf(parts.cup):-1;
    if(rank<0)return null;
    return {...parts,score:rank*10000+parts.band};
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
  function cupLabelSummary(roster,system='uk'){
    if(!['uk','us','eu'].includes(system))system='uk';
    const order=cupOrders[system],counts=new Map(),estimated=new Set();let total=0,count=0,estimatedCount=0;
    for(const d of roster){
      const raw=d[system],parts=sizeParts(raw);if(!parts)continue;
      const cup=system==='us'?({E:'DD',F:'DDD',G:'DDDD'}[parts.cup]||parts.cup):parts.cup,index=order.indexOf(cup);
      if(index<0)continue;total+=index;count++;if(raw.startsWith('≈')){estimatedCount++;estimated.add(cup);}
      counts.set(cup,(counts.get(cup)||0)+1);
    }
    const bins=[...counts].map(([cup,count])=>({cup,count,estimated:estimated.has(cup)})).sort((a,b)=>order.indexOf(a.cup)-order.indexOf(b.cup));
    const peak=Math.max(0,...bins.map(b=>b.count)),meanIndex=count?total/count:null;
    return {count,estimatedCount,bins,modes:bins.filter(b=>b.count===peak).map(b=>b.cup),modeCount:peak,meanIndex,meanLabel:count?order[Math.round(meanIndex)]:null};
  }
  function numericSummary(values){
    const sorted=values.filter(v=>v!=null).sort((a,b)=>a-b),n=sorted.length;
    return {count:n,median:quantile(sorted,.5),q1:quantile(sorted,.25),q3:quantile(sorted,.75)};
  }
  function quantile(sorted,p){
    if(!sorted.length)return null;
    const i=(sorted.length-1)*p,lo=Math.floor(i),hi=Math.ceil(i);
    return sorted[lo]+(sorted[hi]-sorted[lo])*(i-lo);
  }
  function cupMatrix(roster,system='uk'){
    if(!['uk','us','eu'].includes(system))system='uk';
    const sizes=roster.map(d=>({d,s:system==='uk'?cupSize(d.uk):sizeParts(d[system])})).filter(x=>x.s);
    const bands=[...new Set(sizes.map(x=>x.s.band))].sort((a,b)=>a-b);
    const cups=cupDistribution(roster,system).bins.map(b=>b.cup);
    const cells=bands.flatMap(band=>cups.map(cup=>({band,cup,slugs:sizes.filter(x=>x.s.band===band&&x.s.cup===cup).map(x=>x.d.slug)})));
    return {bands,cups,cells};
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
      let score=0,total=0;const components=[];
      for(const key of Object.keys(fields)){
        const w=chosen[key]||0, a=value(source,key,basis), b=value(d,key,basis);
        if(!Number.isFinite(w)||w<=0||a==null||b==null) continue;
        const difference=Math.abs(a-b),weighted=w*difference/spans[key];
        score+=weighted; total+=w;components.push({key,difference,weight:w,contribution:weighted});
      }
      return {d,score:total ? score/total : null,components:components.map(c=>({...c,weight:c.weight/total,contribution:c.contribution/total}))};
    }).filter(x=>x.score!=null).sort((a,b)=>a.score-b.score);
  }
  function distribution(values,count=10){
    const vs=values.filter(v=>v!=null&&Number.isFinite(v)).sort((a,b)=>a-b), n=vs.length;
    if(!n) return {count:0,median:null,bins:[]};
    const lo=vs[0],hi=vs[n-1],size=lo===hi?1:count,step=(hi-lo)/size;
    const bins=Array.from({length:size},(_,i)=>({lo:lo+i*step,hi:lo+(i+1)*step,count:0}));
    bins[bins.length-1].hi=hi;
    for(const v of vs) bins[step ? Math.min(size-1,Math.floor((v-lo)/step)) : 0].count++;
    return {count:n,median:(vs[Math.floor((n-1)/2)]+vs[Math.floor(n/2)])/2,bins};
  }
  function binIndex(value,bins){
    if(!Number.isFinite(value)||!bins.length)return -1;
    const lo=bins[0].lo,hi=bins[bins.length-1].hi;
    if(value<lo||value>hi)return -1;
    return hi===lo?0:Math.min(bins.length-1,Math.floor((value-lo)/((hi-lo)/bins.length)));
  }
  function ratio(d,numerator,denominator){
    const a=value(d,numerator),b=value(d,denominator);
    return a!=null&&b>0?a/b:null;
  }
  function relationship(pairs){
    const points=pairs.filter(p=>p[0]!=null&&p[1]!=null),n=points.length;
    if(n<3)return {count:n,r:null,slope:null,intercept:null};
    const mx=points.reduce((s,p)=>s+p[0],0)/n,my=points.reduce((s,p)=>s+p[1],0)/n;
    let xx=0,yy=0,xy=0;
    for(const [x,y] of points){xx+=(x-mx)**2;yy+=(y-my)**2;xy+=(x-mx)*(y-my);}
    if(!xx||!yy)return {count:n,r:null,slope:null,intercept:null};
    return {count:n,r:Math.max(-1,Math.min(1,xy/Math.sqrt(xx*yy))),slope:xy/xx,intercept:my-xy/xx*mx};
  }
  function rangeFailures(d,ranges){
    return Object.entries(ranges).flatMap(([field,[lo,hi]])=>{
      const v=d[field];
      return v==null?[{field,value:null,limit:null}]:v<lo-1e-6?[{field,value:v,limit:lo}]:v>hi+1e-6?[{field,value:v,limit:hi}]:[];
    });
  }
  function percentile(v,values){
    const known=values.filter(x=>x!=null);
    if(v==null||!known.length)return null;
    if(known.length===1)return .5;
    const below=known.filter(x=>x<v).length,equal=known.filter(x=>x===v).length;
    return (below+(equal-1)/2)/(known.length-1);
  }
  function percentileAt(v,values){
    const sorted=values.filter(x=>x!=null).sort((a,b)=>a-b),n=sorted.length;
    if(!n)return null;if(n===1)return .5;
    if(v<=sorted[0])return 0;if(v>=sorted[n-1])return 1;
    if(sorted.includes(v))return percentile(v,sorted);
    const hi=sorted.findIndex(x=>x>v),lo=hi-1;
    return (lo+(v-sorted[lo])/(sorted[hi]-sorted[lo]))/(n-1);
  }
  function percentileRange(values,lo,hi){
    const sorted=values.filter(v=>v!=null).sort((a,b)=>a-b);
    return sorted.length?[quantile(sorted,lo),quantile(sorted,hi)]:null;
  }
  return {fields,weights,sizeParts,cupSize,cupLabelSummary,numericSummary,cupDistribution,cupMatrix,percentage,value,displayed,difference,outcome,gameOutcome,matches,distribution,binIndex,ratio,relationship,rangeFailures,percentile,percentileAt,percentileRange};
})();
if(typeof module!=='undefined')module.exports=Analysis;
