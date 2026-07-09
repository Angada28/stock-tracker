"""
export_html.py -- generate the interactive HTML dashboard.
"""
import json
import math
import pandas as pd
from datetime import date
from pathlib import Path

BASE      = Path(__file__).parent
HTML_PATH = BASE / "dashboard.html"

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """\
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0d1117;color:#e2e8f0;height:100vh;display:flex;flex-direction:column}
#app{display:flex;flex-direction:column;height:100vh;overflow:hidden}
header{padding:12px 20px;border-bottom:1px solid #1e293b;display:flex;align-items:center;gap:16px;flex-shrink:0}
header h1{font-size:1.1rem;font-weight:700;color:#f1f5f9}
.hstats{display:flex;gap:14px;font-size:11px;color:#64748b}
.hstats strong{color:#94a3b8}
nav{display:flex;gap:2px;padding:0 20px;border-bottom:1px solid #1e293b;flex-shrink:0}
.nav-btn{padding:9px 16px;font-size:.85rem;color:#64748b;border:none;background:none;cursor:pointer;
         border-bottom:2px solid transparent;transition:all .15s}
.nav-btn:hover{color:#94a3b8}
.nav-btn.on{color:#f1f5f9;border-bottom-color:#3b82f6}
#content{flex:1;overflow:auto;padding:20px}
.panel{display:none}.panel.on{display:block}
/* Table */
.tbl-wrap{border-radius:8px;border:1px solid #1e293b;overflow:auto;max-height:calc(100vh - 200px)}
table{width:100%;border-collapse:collapse;font-size:.82rem}
thead tr{position:sticky;top:0;z-index:2}
th{padding:9px 12px;background:#161c27;color:#64748b;font-weight:600;font-size:.72rem;
   text-transform:uppercase;letter-spacing:.05em;white-space:nowrap;cursor:pointer;user-select:none;
   border-right:1px solid #1a2332;border-bottom:2px solid #1e293b}
th:hover{color:#94a3b8}
th .sort-arrow{margin-left:4px;opacity:.4}
th.sorted .sort-arrow{opacity:1}
td{padding:8px 12px;border-bottom:1px solid #1e293b;border-right:1px solid #1a2332;white-space:nowrap}
tbody tr:nth-child(even) td{background:#0f1820}
tr:hover td{background:#1e293b99!important;cursor:pointer}
.pos{color:#4ade80;font-weight:600}.neg{color:#f87171;font-weight:600}
.sym-cell{font-weight:700;color:#60a5fa}
/* Search */
.toolbar{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.search{background:#1e293b;border:1px solid #334155;border-radius:6px;
        color:#e2e8f0;font-size:.85rem;padding:7px 12px;width:220px;outline:none}
.search:focus{border-color:#3b82f6}
/* Range picker */
.range-bar{display:flex;align-items:center;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.range-bar label{font-size:11px;color:#64748b}
.rbtn{padding:4px 11px;border-radius:5px;font-size:.8rem;cursor:pointer;
      border:1px solid #334155;background:#1e293b;color:#64748b;transition:all .12s}
.rbtn:hover{color:#94a3b8}
.rbtn.on{background:#3b82f6;border-color:#3b82f6;color:#fff;font-weight:600}
.date-inp{background:#1e293b;border:1px solid #334155;border-radius:5px;
          color:#e2e8f0;font-size:.8rem;padding:4px 8px;width:115px;outline:none}
.date-inp:focus{border-color:#3b82f6}
/* Detail view */
.back-btn{display:inline-flex;align-items:center;gap:5px;font-size:.82rem;color:#64748b;
          cursor:pointer;margin-bottom:16px;border:none;background:none;padding:0}
.back-btn:hover{color:#94a3b8}
.detail-header{display:flex;align-items:baseline;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.detail-sym{font-size:1.4rem;font-weight:700;color:#f1f5f9}
.detail-name{font-size:.9rem;color:#64748b}
.detail-price{font-size:1.3rem;font-weight:600}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:18px}
.metric{background:#1e293b;border-radius:8px;padding:10px 14px}
.metric-label{font-size:.72rem;color:#64748b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.metric-val{font-size:1rem;font-weight:600;color:#f1f5f9}
.chart-card{background:#1e293b;border-radius:8px;padding:16px;margin-bottom:14px}
.chart-card h3{font-size:.8rem;color:#64748b;margin-bottom:12px;text-transform:uppercase;letter-spacing:.05em}
/* Compare */
.cmp-search-row{display:flex;align-items:center;gap:8px;margin-bottom:10px;position:relative}
.cmp-search{background:#1e293b;border:1px solid #334155;border-radius:6px;
            color:#e2e8f0;font-size:.85rem;padding:7px 12px;width:200px;outline:none}
.cmp-search:focus{border-color:#3b82f6}
.cmp-dropdown{position:absolute;top:36px;left:0;width:220px;background:#161c27;
              border:1px solid #334155;border-radius:6px;z-index:10;max-height:200px;
              overflow-y:auto;display:none}
.cmp-drop-item{padding:7px 12px;font-size:.82rem;cursor:pointer;color:#e2e8f0}
.cmp-drop-item:hover{background:#334155}
.cmp-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;min-height:28px}
.chip{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;
      font-size:.78rem;font-weight:600;border:1px solid transparent}
.chip-x{cursor:pointer;opacity:.6;font-size:.85rem;line-height:1;margin-left:2px}
.chip-x:hover{opacity:1}
.compare-tbl{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:16px}
.compare-tbl th{padding:8px 12px;text-align:left;color:#64748b;font-size:.72rem;
                text-transform:uppercase;border-bottom:1px solid #1e293b}
.compare-tbl td{padding:8px 12px;border-bottom:1px solid #1e293b40}
/* Light mode */
body.light{background:#f8fafc;color:#1e293b}
body.light header{border-bottom-color:#cbd5e1;background:#ffffff}
body.light header h1{color:#0f172a}
body.light .hstats strong{color:#334155}
body.light nav{border-bottom-color:#cbd5e1;background:#ffffff}
body.light .nav-btn{color:#64748b}
body.light .nav-btn:hover{color:#334155}
body.light .nav-btn.on{color:#0f172a;border-bottom-color:#3b82f6}
body.light #content{background:#f8fafc}
body.light .tbl-wrap{border-color:#cbd5e1}
body.light th{background:#e2e8f0;color:#475569;border-right-color:#cbd5e1;border-bottom-color:#94a3b8}
body.light th:hover{color:#1e293b}
body.light td{border-bottom-color:#e2e8f0;border-right-color:#cbd5e1;color:#1e293b}
body.light tbody tr:nth-child(even) td{background:#f1f5f9}
body.light tr:hover td{background:#dde4ee99!important}
body.light .sym-cell{color:#2563eb}
body.light .search{background:#ffffff;border-color:#cbd5e1;color:#0f172a}
body.light .rbtn{background:#ffffff;border-color:#cbd5e1;color:#475569}
body.light .rbtn:hover{color:#1e293b}
body.light .rbtn.on{background:#3b82f6;border-color:#3b82f6;color:#fff}
body.light .date-inp{background:#ffffff;border-color:#cbd5e1;color:#0f172a}
body.light .back-btn{color:#64748b}
body.light .back-btn:hover{color:#334155}
body.light .detail-sym{color:#0f172a}
body.light .detail-name{color:#64748b}
body.light .metric{background:#e2e8f0}
body.light .metric-label{color:#64748b}
body.light .metric-val{color:#0f172a}
body.light .chart-card{background:#e8edf3}
body.light .chart-card h3{color:#475569}
body.light .cmp-search{background:#ffffff;border-color:#cbd5e1;color:#0f172a}
body.light .cmp-dropdown{background:#ffffff;border-color:#cbd5e1}
body.light .cmp-drop-item{color:#0f172a}
body.light .cmp-drop-item:hover{background:#e2e8f0}
body.light .compare-tbl th{color:#475569;border-bottom-color:#cbd5e1}
body.light .compare-tbl td{border-bottom-color:#e2e8f044;color:#1e293b}
body.light .movers-section h3{color:#475569}
body.light .mover-bar-wrap{background:#e2e8f0}
body.light .mover-sym{color:#2563eb}
body.light .range-bar label{color:#64748b}
body.light #theme-toggle{background:#e2e8f0;border-color:#94a3b8;color:#334155}
body.light .pos{color:#16a34a}
body.light .neg{color:#dc2626}
/* Movers */
.movers-section h3{font-size:.8rem;color:#64748b;text-transform:uppercase;
                   letter-spacing:.05em;margin-bottom:10px}
.mover-row{display:flex;align-items:center;gap:8px;padding:7px 0;
           border-bottom:1px solid #1e293b40;cursor:pointer}
.mover-row:hover .mover-sym{text-decoration:underline}
.mover-bar-wrap{flex:1;height:6px;background:#1e293b;border-radius:3px;overflow:hidden}
.mover-bar{height:100%;border-radius:3px;transition:width .3s}
.mover-sym{font-size:.82rem;font-weight:700;color:#60a5fa;min-width:52px}
.mover-pct{font-size:.82rem;font-weight:600;min-width:58px;text-align:right}
"""

# ---------------------------------------------------------------------------
# JavaScript  (raw string -- no Python escape processing)
# ---------------------------------------------------------------------------
JS = r"""
const D=DATA.symbols, TODAY=DATA.today, UPDATED=DATA.updated;
const COLORS=["#3b82f6","#4ade80","#f59e0b","#f87171","#a78bfa","#34d399",
              "#fb923c","#60a5fa","#e879f9","#fbbf24","#818cf8","#2dd4bf",
              "#f472b6","#a3e635","#38bdf8","#fb7185","#c084fc","#fdba74",
              "#86efac","#67e8f9"];
let view='today', detailSym=null, cmpSyms=new Set();
let range='M1', customFrom='', customTo='';
let sortCol='vol', sortAsc=false;
let charts={};

// -- Utilities --
function fmtPct(v,sign=true){if(v==null)return'--';return(sign&&v>0?'+':'')+v.toFixed(2)+'%';}
function fmtPrice(v){if(v==null)return'--';return'$'+v.toFixed(2);}
function fmtMcap(v){
  if(v==null)return'--';
  if(v>=1e12)return(v/1e12).toFixed(2)+'T';
  if(v>=1e9) return(v/1e9).toFixed(2)+'B';
  if(v>=1e6) return(v/1e6).toFixed(2)+'M';
  return v.toLocaleString();
}
function fmtVol(v){if(v==null)return'--';return(v/1e6).toFixed(1)+'M';}
function cls(v){if(v==null)return'';return v>=0?'pos':'neg';}
function destroyChart(id){if(charts[id]){charts[id].destroy();delete charts[id];}}

// -- Filter history by range --
function filterHist(sym,r,cf,ct){
  var hist=D[sym].history;
  if(!hist.length)return[];
  var last=hist[hist.length-1].date;
  if(r==='Custom'){
    var f=cf||hist[0].date, t=ct||last;
    return hist.filter(function(h){return h.date>=f&&h.date<=t;});
  }
  var days={W1:7,M1:30,M3:90,ALL:99999}[r]||30;
  var cutoff=new Date(last); cutoff.setDate(cutoff.getDate()-days);
  var cs=cutoff.toISOString().slice(0,10);
  return hist.filter(function(h){return h.date>=cs;});
}

// -- Nav --
function goView(v,sym){
  view=v; detailSym=sym||null;
  document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('on');});
  document.querySelectorAll('.nav-btn').forEach(function(b){b.classList.remove('on');});
  document.getElementById('panel-'+v).classList.add('on');
  var nb=document.getElementById('nav-'+v);
  if(nb)nb.classList.add('on');
  if(v==='today')renderToday();
  else if(v==='detail')renderDetail();
  else if(v==='compare')renderCompare();
  else if(v==='movers')renderMovers();
}

// -- Range bar --
function makeRangeBar(containerId,cbName){
  var c=document.getElementById(containerId);
  if(!c)return;
  var opts=['W1','M1','M3','ALL','Custom'];
  var labels={W1:'1W',M1:'1M',M3:'3M',ALL:'All',Custom:'Custom'};
  var html='<div class="range-bar"><label>Range:</label>';
  opts.forEach(function(o){
    html+='<button class="rbtn'+(range===o?' on':'')+'" onclick="setRange(\''+o+'\',\''+containerId+'\',\''+cbName+'\')">'+labels[o]+'</button>';
  });
  html+='<span id="custom-dates-'+containerId+'" style="display:'+(range==='Custom'?'flex':'none')+';align-items:center;gap:6px">'
       +'<input class="date-inp" type="date" id="cf-'+containerId+'" value="'+customFrom+'" data-cb="'+cbName+'" onchange="customFrom=this.value;window[this.dataset.cb]()">'
       +'<span style="color:#64748b;font-size:.8rem">to</span>'
       +'<input class="date-inp" type="date" id="ct-'+containerId+'" value="'+customTo+'" data-cb="'+cbName+'" onchange="customTo=this.value;window[this.dataset.cb]()">'
       +'</span></div>';
  c.innerHTML=html;
}
function setRange(r,containerId,cbName){
  range=r;
  document.querySelectorAll('#'+containerId+' .rbtn').forEach(function(b){b.classList.remove('on');});
  event.target.classList.add('on');
  var cd=document.getElementById('custom-dates-'+containerId);
  if(cd)cd.style.display=r==='Custom'?'flex':'none';
  if(r!=='Custom')window[cbName]();
}

// -- TODAY view --
function renderToday(){
  var cols=[
    {key:'sym',     label:'Symbol' },
    {key:'name',    label:'Name'   },
    {key:'price',   label:'Price'  },
    {key:'pct',     label:'Day %'  },
    {key:'vol',     label:'Volume' },
    {key:'mcap',    label:'Mkt Cap'},
    {key:'pe',      label:'P/E TTM'},
    {key:'wk52pct', label:'52W %'  },
  ];
  var rows=TODAY.map(function(sym){
    var h=D[sym]; var last=h.history[h.history.length-1]||{};
    return {sym:sym,name:h.name,price:last.price,pct:last.pct,
            vol:last.vol,mcap:last.mcap,pe:last.pe,wk52pct:last.wk52pct};
  });
  var q=document.getElementById('today-search').value.toLowerCase();
  if(q)rows=rows.filter(function(r){return r.sym.toLowerCase().indexOf(q)>=0||r.name.toLowerCase().indexOf(q)>=0;});
  rows.sort(function(a,b){
    var av=a[sortCol],bv=b[sortCol];
    if(typeof av==='string')av=av.toLowerCase();
    if(typeof bv==='string')bv=bv.toLowerCase();
    if(av==null)return 1; if(bv==null)return -1;
    return sortAsc?(av>bv?1:-1):(av<bv?1:-1);
  });
  var thead='<tr>';
  cols.forEach(function(c){
    var isSorted=sortCol===c.key;
    thead+='<th class="'+(isSorted?'sorted':'')+'" onclick="setSortCol(\''+c.key+'\')">'+c.label+'<span class="sort-arrow">'+(isSorted?(sortAsc?'^':'v'):'v')+'</span></th>';
  });
  thead+='</tr>';
  var tbody='';
  rows.forEach(function(r){
    tbody+='<tr onclick="goView(\'detail\',\''+r.sym+'\')">'
          +'<td class="sym-cell">'+r.sym+'</td>'
          +'<td>'+r.name+'</td>'
          +'<td>'+fmtPrice(r.price)+'</td>'
          +'<td class="'+cls(r.pct)+'">'+fmtPct(r.pct)+'</td>'
          +'<td>'+fmtVol(r.vol)+'</td>'
          +'<td>'+fmtMcap(r.mcap)+'</td>'
          +'<td>'+(r.pe!=null?r.pe.toFixed(1):'--')+'</td>'
          +'<td class="'+cls(r.wk52pct)+'">'+fmtPct(r.wk52pct)+'</td>'
          +'</tr>';
  });
  document.getElementById('today-table').innerHTML='<thead>'+thead+'</thead><tbody>'+tbody+'</tbody>';
}
function setSortCol(col){
  if(sortCol===col)sortAsc=!sortAsc; else{sortCol=col;sortAsc=false;}
  renderToday();
}

// -- DETAIL view --
function renderDetail(){
  var sym=detailSym;
  if(!sym||!D[sym]){goView('today');return;}
  var info=D[sym];
  var hist=filterHist(sym,range,customFrom,customTo);
  var last=hist.length?hist[hist.length-1]:{};
  var pctCls=cls(last.pct);
  document.getElementById('detail-sym').textContent=sym;
  document.getElementById('detail-name').textContent=info.name;
  document.getElementById('detail-price').innerHTML=
    '<span>'+fmtPrice(last.price)+'</span> <span class="'+pctCls+'" style="font-size:.9rem">'+fmtPct(last.pct)+' today</span>';
  document.getElementById('detail-metrics').innerHTML=
    '<div class="metric"><div class="metric-label">Market Cap</div><div class="metric-val">'+fmtMcap(last.mcap)+'</div></div>'
   +'<div class="metric"><div class="metric-label">P/E Ratio (TTM)</div><div class="metric-val">'+(last.pe!=null?last.pe.toFixed(1):'--')+'</div></div>'
   +'<div class="metric"><div class="metric-label">52W Change</div><div class="metric-val '+cls(last.wk52pct)+'">'+fmtPct(last.wk52pct)+'</div></div>'
   +'<div class="metric"><div class="metric-label">52W Range</div><div class="metric-val" style="font-size:.85rem">'+(last.wk52lo!=null&&last.wk52hi!=null?'$'+last.wk52lo.toFixed(0)+' - $'+last.wk52hi.toFixed(0):'--')+'</div></div>'
   +'<div class="metric"><div class="metric-label">Volume</div><div class="metric-val">'+fmtVol(last.vol)+'</div></div>';
  makeRangeBar('detail-range','renderDetail');
  var labels=hist.map(function(h){return h.date;});
  var prices=hist.map(function(h){return h.price;});
  var vols=hist.map(function(h){return h.vol;});
  destroyChart('priceChart');
  charts['priceChart']=new Chart(document.getElementById('priceChart'),{
    type:'line',
    data:{labels:labels,datasets:[{label:'Price',data:prices,borderColor:'#3b82f6',
      backgroundColor:'#3b82f610',fill:true,tension:.3,
      pointRadius:hist.length>60?0:3,pointHoverRadius:5,borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return' $'+c.parsed.y.toFixed(2);}}}},
      scales:{x:{grid:{color:gc()},ticks:{color:tc(),maxTicksLimit:8}},
              y:{grid:{color:gc()},ticks:{color:tc(),callback:function(v){return'$'+v.toFixed(0);}}}}}
  });
  destroyChart('volChart');
  charts['volChart']=new Chart(document.getElementById('volChart'),{
    type:'bar',
    data:{labels:labels,datasets:[{label:'Volume',data:vols,backgroundColor:'#3b82f655',borderColor:'#3b82f6',borderWidth:1}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return' '+fmtVol(c.parsed.y);}}}},
      scales:{x:{grid:{color:gc()},ticks:{color:tc(),maxTicksLimit:8}},
              y:{grid:{color:gc()},ticks:{color:tc(),callback:function(v){return fmtVol(v);}}}}}
  });
}

// -- COMPARE view --
function renderCompare(){
  renderCmpChips();
  makeRangeBar('cmp-range','renderCompareChart');
  renderCompareChart();
  setupCmpSearch();
}
function renderCmpChips(){
  var el=document.getElementById('cmp-chips');
  if(!el)return;
  if(!cmpSyms.size){
    el.innerHTML='<span style="font-size:.78rem;color:#475569">Type a symbol above to add it to the chart</span>';
    return;
  }
  var html='';
  var arr=Array.from(cmpSyms);
  arr.forEach(function(sym,i){
    var col=COLORS[i%COLORS.length];
    html+='<span class="chip" style="background:'+col+'22;border-color:'+col+';color:'+col+'">'
         +sym+'<span class="chip-x" onclick="removeCmp(\''+sym+'\')">x</span></span>';
  });
  el.innerHTML=html;
}
function removeCmp(sym){cmpSyms.delete(sym);renderCmpChips();renderCompareChart();}
function addCmp(sym){
  if(D[sym])cmpSyms.add(sym);
  var inp=document.getElementById('cmp-search'); if(inp)inp.value='';
  var dd=document.getElementById('cmp-dropdown'); if(dd)dd.style.display='none';
  renderCmpChips();renderCompareChart();
}
function setupCmpSearch(){
  var inp=document.getElementById('cmp-search');
  var dd=document.getElementById('cmp-dropdown');
  if(!inp||inp._bound)return;
  inp._bound=true;
  var allSyms=Object.keys(D).sort();
  inp.addEventListener('input',function(){
    var q=this.value.trim().toUpperCase();
    if(!q){dd.style.display='none';return;}
    var hits=allSyms.filter(function(s){
      return !cmpSyms.has(s)&&(s.indexOf(q)===0||D[s].name.toUpperCase().indexOf(q)>=0);
    }).slice(0,10);
    if(!hits.length){dd.style.display='none';return;}
    dd.innerHTML=hits.map(function(s){
      return '<div class="cmp-drop-item" onmousedown="addCmp(\''+s+'\')">'+s
            +' <span style="color:#64748b;font-size:.75rem">'+D[s].name+'</span></div>';
    }).join('');
    dd.style.display='block';
  });
  inp.addEventListener('blur',function(){setTimeout(function(){dd.style.display='none';},150);});
  inp.addEventListener('keydown',function(e){
    if(e.key==='Enter'){var q=this.value.trim().toUpperCase();if(D[q])addCmp(q);}
  });
}
function renderCompareChart(){
  var syms=Array.from(cmpSyms);
  var datasets=[];
  var summaryRows='';
  syms.forEach(function(sym,i){
    var hist=filterHist(sym,range,customFrom,customTo);
    if(hist.length<2)return;
    var base=hist[0].price;
    var col=COLORS[i%COLORS.length];
    datasets.push({label:sym,
      data:hist.map(function(h){return{x:h.date,y:base?+((h.price-base)/base*100).toFixed(2):0};}),
      borderColor:col,backgroundColor:'transparent',
      tension:.3,pointRadius:hist.length>60?0:2,pointHoverRadius:5,borderWidth:2});
    var last=hist[hist.length-1];
    var chg=base?((last.price-base)/base*100):0;
    summaryRows+='<tr>'
      +'<td style="color:'+col+';font-weight:700">'+sym+'</td>'
      +'<td>'+D[sym].name+'</td>'
      +'<td>'+fmtPrice(hist[0].price)+'</td>'
      +'<td>'+fmtPrice(last.price)+'</td>'
      +'<td class="'+cls(chg)+'">'+fmtPct(chg)+'</td>'
      +'</tr>';
  });
  destroyChart('cmpChart');
  charts['cmpChart']=new Chart(document.getElementById('cmpChart'),{
    type:'line',data:{datasets:datasets},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{labels:{color:tc(),boxWidth:12}},
        tooltip:{callbacks:{label:function(c){return' '+c.dataset.label+': '+(c.parsed.y>=0?'+':'')+c.parsed.y.toFixed(2)+'%';}}}},
      scales:{x:{type:'category',grid:{color:gc()},ticks:{color:tc(),maxTicksLimit:8}},
              y:{grid:{color:gc()},ticks:{color:tc(),callback:function(v){return(v>=0?'+':'')+v+'%';}}}}}
  });
  document.getElementById('cmp-table').innerHTML=
    '<thead><tr><th>Symbol</th><th>Name</th><th>Start</th><th>End</th><th>Change</th></tr></thead>'
    +'<tbody>'+summaryRows+'</tbody>';
}

// -- MOVERS view --
function renderMovers(){makeRangeBar('movers-range','renderMoversContent');renderMoversContent();}
function renderMoversContent(){
  var syms=Object.keys(D);
  var results=[];
  syms.forEach(function(sym){
    var hist=filterHist(sym,range,customFrom,customTo);
    if(!hist.length)return;
    var vols=hist.map(function(h){return h.vol||0;}).filter(function(v){return v>0;});
    if(!vols.length)return;
    var avgVol=vols.reduce(function(a,b){return a+b;},0)/vols.length;
    results.push({sym:sym,vol:avgVol});
  });
  results.sort(function(a,b){return b.vol-a.vol;});
  var top=results.slice(0,20);
  var noData='<p style="color:#475569;font-size:.82rem;padding:8px 0">No volume data available for this range.</p>';
  if(!top.length){document.getElementById('gainers').innerHTML=noData;return;}
  var maxVol=top[0].vol;
  document.getElementById('gainers').innerHTML=top.map(function(r){
    var w=Math.round(r.vol/maxVol*100);
    return '<div class="mover-row" onclick="goView(\'detail\',\''+r.sym+'\')">'+
           '<span class="mover-sym">'+r.sym+'</span>'+
           '<div class="mover-bar-wrap"><div class="mover-bar" style="width:'+w+'%;background:#3b82f655;border-right:2px solid #3b82f6"></div></div>'+
           '<span class="mover-pct">'+fmtVol(r.vol)+'</span>'+
           '</div>';
  }).join('');
}


// -- Theme toggle --
function isLight(){return document.body.classList.contains('light');}
function gc(){return isLight()?'#cbd5e1':'#1e293b';}
function tc(){return isLight()?'#475569':'#64748b';}
function toggleTheme(){
  var light=document.body.classList.toggle('light');
  localStorage.setItem('theme',light?'light':'dark');
  document.getElementById('theme-toggle').textContent=light?'Dark':'Light';
  if(view==='detail'&&detailSym)renderDetail();
  if(view==='compare')renderCompareChart();
  if(view==='movers')renderMovers();
}
(function(){
  if(localStorage.getItem('theme')==='light'){
    document.body.classList.add('light');
    document.getElementById('theme-toggle').textContent='Dark';
  }
})();
// -- Boot --
document.getElementById('today-search').addEventListener('input',renderToday);
goView('today');
"""

# ---------------------------------------------------------------------------
# HTML body structure
# ---------------------------------------------------------------------------
BODY = """\
<div id='app'>
<header>
  <h1>&#x1F4C8; Stock Tracker</h1>
  <div class='hstats' id='hstats'></div>
  <a id='dl-btn' href='excel/stocks_{today}.xlsx' download style='margin-left:auto;padding:5px 12px;border-radius:5px;border:1px solid #334155;background:#1e293b;color:#94a3b8;font-size:.78rem;cursor:pointer;text-decoration:none'>&#8595; Excel</a>
  <button id='theme-toggle' onclick='toggleTheme()' style='padding:5px 12px;border-radius:5px;border:1px solid #334155;background:#1e293b;color:#94a3b8;font-size:.78rem;cursor:pointer'>Light</button>
</header>
<nav>
  <button id='nav-today'   class='nav-btn' onclick="goView('today')">Today</button>
  <button id='nav-detail'  class='nav-btn' onclick="goView('detail',detailSym||TODAY[0])">Detail</button>
  <button id='nav-compare' class='nav-btn' onclick="goView('compare')">Compare</button>
  <button id='nav-movers'  class='nav-btn' onclick="goView('movers')">Movers</button>
</nav>
<div id='content'>

  <div id='panel-today' class='panel'>
    <div class='toolbar'>
      <input class='search' id='today-search' placeholder='Search symbol or name...'>
    </div>
    <div class='tbl-wrap'><table id='today-table'></table></div>
  </div>

  <div id='panel-detail' class='panel'>
    <button class='back-btn' onclick="goView('today')">&#8592; Back to Today</button>
    <div class='detail-header'>
      <span class='detail-sym' id='detail-sym'></span>
      <span class='detail-name' id='detail-name'></span>
      <span class='detail-price' id='detail-price'></span>
    </div>
    <div class='metrics' id='detail-metrics'></div>
    <div id='detail-range'></div>
    <div class='chart-card'><h3>Price</h3><div style='height:220px'><canvas id='priceChart'></canvas></div></div>
    <div class='chart-card'><h3>Volume</h3><div style='height:120px'><canvas id='volChart'></canvas></div></div>
  </div>

  <div id='panel-compare' class='panel'>
    <div class='cmp-search-row'>
      <input class='cmp-search' id='cmp-search' placeholder='Add symbol...' autocomplete='off'>
      <div class='cmp-dropdown' id='cmp-dropdown'></div>
    </div>
    <div class='cmp-chips' id='cmp-chips'></div>
    <div id='cmp-range'></div>
    <div class='chart-card'><h3>% change from period start</h3><div style='height:280px'><canvas id='cmpChart'></canvas></div></div>
    <table class='compare-tbl' id='cmp-table'></table>
  </div>

  <div id='panel-movers' class='panel'>
    <div id='movers-range'></div>
    <div class='movers-section'><h3>Most Active by Volume</h3><div id='gainers'></div></div>
  </div>

</div>
</div>
"""


# ---------------------------------------------------------------------------
# Generation function
# ---------------------------------------------------------------------------
def _safe(x):
    """Return None for NaN/None, otherwise the value."""
    if x is None:
        return None
    try:
        if math.isnan(float(x)):
            return None
    except Exception:
        pass
    return x


def export_html(conn):
    df = pd.read_sql_query("""
        SELECT dp.date, dp.symbol, s.name,
               dp.price, dp.change, dp.change_pct,
               dp.volume, dp.market_cap, dp.pe_ratio,
               dp.wk52_change_pct, dp.wk52_low, dp.wk52_high, dp.source
        FROM   daily_prices dp
        JOIN   stocks s ON s.symbol = dp.symbol
        ORDER  BY dp.symbol, dp.date
    """, conn)

    if df.empty:
        print("  No data yet -- skipping HTML export.")
        return

    today_str = date.today().isoformat()

    # Build per-symbol history
    sym_data = {}
    for sym, sdf in df.groupby("symbol"):
        sdf = sdf.sort_values("date")
        sym_data[sym] = {
            "name": sdf.iloc[0]["name"],
            "history": [
                {
                    "date":    row["date"],
                    "price":   _safe(row["price"]),
                    "change":  _safe(row["change"]),
                    "pct":     _safe(row["change_pct"]),
                    "vol":     int(row["volume"]) if pd.notna(row["volume"]) and row["volume"] else None,
                    "mcap":    int(row["market_cap"]) if pd.notna(row["market_cap"]) and row["market_cap"] else None,
                    "pe":      _safe(row["pe_ratio"]),
                    "wk52pct": _safe(row["wk52_change_pct"]),
                    "wk52lo":  _safe(row["wk52_low"]),
                    "wk52hi":  _safe(row["wk52_high"]),
                }
                for _, row in sdf.iterrows()
                if pd.notna(row["price"]) and row["price"] is not None
            ],
        }

    # Today's symbols ordered by volume
    today_df   = df[df["date"] == today_str].copy()
    today_df   = today_df.sort_values("volume", ascending=False, na_position="last")
    today_list = today_df["symbol"].tolist()

    n_active  = int((today_df["source"] == "most_active").sum()) if "source" in today_df.columns else len(today_df)
    n_tracked = len(sym_data)

    embedded = json.dumps(
        {"symbols": sym_data, "today": today_list, "updated": today_str},
        separators=(",", ":"),
    )

    # Stats line injected via JS so we can reuse BODY constant
    stats_js = (
        "document.getElementById('hstats').innerHTML="
        "'<span><strong>" + today_str + "</strong></span>"
        "<span><strong>" + str(n_active) + "</strong> most active today</span>"
        "<span><strong>" + str(n_tracked) + "</strong> symbols tracked</span>';"
    )

    html = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Stock Tracker</title>"
        "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'></script>"
        "<style>" + CSS + "</style>"
        "</head><body>"
        + BODY.replace('{today}', today_str) +
        "<script>const DATA=" + embedded + ";</script>"
        "<script>" + stats_js + JS + "</script>"
        "</body></html>"
    )

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"  HTML saved -> {HTML_PATH}  ({len(html)//1024} KB, {n_tracked} symbols, {len(df)} rows)")
