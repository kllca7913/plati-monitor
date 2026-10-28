/* Full hourly history view (shared by Plati 每小时 tab and FunPay tabs). Never sums across sellers. */
var HS={};
function hP2(n){return (n<10?"0":"")+n}
function hMD(ms){var d=new Date(ms);return hP2(d.getUTCMonth()+1)+"-"+hP2(d.getUTCDate())}
function hISO(ms){return new Date(ms).toISOString().slice(0,10)}
function hHM(ms){var d=new Date(ms);return hP2(d.getUTCHours())+":"+hP2(d.getUTCMinutes())}
function hRows(src){var rows=[];
 for(var i=src.fts.length-1;i>=0;i--){
  var e=Date.parse(src.fts[i]+":00Z"),p=Date.parse(src.fprev[i]+":00Z"),g=(e-p)/60000,r=Math.round(e/3600000)*3600000,near=Math.abs(e-r)<=20*60000,base=near?r:e,okgap=(g>=40&&g<=80);
  rows.push({i:i,date:hISO(base),label:hMD(base)+" "+hHM(base)+((!near||!okgap)?"*":""),title:"实际采集 "+src.fprev[i].replace("T"," ")+" → "+src.fts[i].replace("T"," ")+"，间隔 "+Math.round(g)+" 分钟",cmp:(near&&okgap),r:r})}
 return rows}
function hCol(v,mx){if(v==null||mx<=0)return "";var a=Math.max(0,v)/mx;return a>0?' style="background:rgba(37,99,235,'+(0.08+0.62*a).toFixed(2)+');color:'+(a>0.6?'#fff':'#222')+'"':""}
function histMount(box,p,src,title,csv){
 var S=HS[p]||(HS[p]={day:null,seller:0}); S.src=src; S.rows=hRows(src);
 var ds={};S.rows.forEach(function(r){ds[r.date]=1});S.dates=Object.keys(ds).sort().reverse();
 if(S.day!=="all"&&S.dates.indexOf(S.day)<0)S.day=S.dates[0]||"all";
 if(S.seller>=src.sellers.length)S.seller=0;
 var dopt='<option value="all"'+(S.day=="all"?" selected":"")+'>全部（'+S.rows.length+' 个时段）</option>';
 S.dates.forEach(function(d){dopt+='<option value="'+d+'"'+(S.day==d?" selected":"")+'>'+d+'</option>'});
 var sopt="";src.sellers.forEach(function(s,i){sopt+='<option value="'+i+'"'+(S.seller==i?" selected":"")+'>'+esc(s.seller)+'</option>'});
 var csvl=csv?' <a href="'+csv+'" download>⬇ 下载完整每小时 CSV（含全部历史）</a>':'';
 document.getElementById(box).innerHTML=
 '<div class="card"><h2>'+esc(title)+' · 每小时完整记录</h2>'+
 '<div style="font-size:12px;margin-bottom:8px">选择日期：<select id="'+p+'_day" onchange="histSet(\''+p+'\',\'day\',this.value)">'+dopt+'</select>'+csvl+'</div>'+
 '<div class="scroll hs"><table id="'+p+'_tbl"></table></div>'+
 '<p class="muted" style="font-size:12px;margin:8px 0 0">每行 = 一个时段的新增订单（近似），时间为该时段结束时刻（北京时间），新到旧排列，历史永久保留；可上下左右滑动，时间列固定。每个日期的第一行是“各卖家自己当天小计”（只累加该卖家有数据的时段，各卖家之间不求和）。“—”= 该时段无有效数据；时间带 * = 两次采集间隔不是约1小时（已按实际时刻显示）。鼠标悬停/长按时间可看实际采集时刻。</p></div>'+
 '<div class="card"><h2>'+esc(title)+' · 对比不同日期（同一卖家，按一天中的小时）</h2>'+
 '<div style="font-size:12px;margin-bottom:8px">选择卖家：<select id="'+p+'_sel" onchange="histSet(\''+p+'\',\'seller\',this.value)">'+sopt+'</select></div>'+
 '<div class="scroll hs"><table id="'+p+'_cmp"></table></div>'+
 '<p class="muted" style="font-size:12px;margin:8px 0 0">行 = 北京时间一天中的小时（如 “3点” = 03:00–04:00），列 = 日期（新到旧）。颜色越深表示该卖家这一格数值越高；“平均”= 该卖家该小时在已有日期里的平均值。只统计间隔约1小时（40–80分钟）的时段；各卖家分开，不做跨卖家合计。</p></div>';
 histRender(p)}
function histSet(p,k,v){var S=HS[p];if(k=="day")S.day=v;else S.seller=parseInt(v,10)||0;histRender(p)}
function histRender(p){var S=HS[p],src=S.src,sl=src.sellers,rows=S.rows;
 var T=document.getElementById(p+"_tbl"),C=document.getElementById(p+"_cmp");if(!T)return;
 if(!rows.length){T.innerHTML='<tr><td class="muted">还没有足够的快照（至少2次）才能计算每小时订单，下一次采集后会显示。</td></tr>';C.innerHTML=T.innerHTML;return}
 var h='<tr><th>时间（北京时间）</th>';sl.forEach(function(s){h+='<th>'+esc(s.seller)+'</th>'});h+='</tr>';
 var cur=null,grp=[];
 var vis=rows.filter(function(r){return S.day=="all"||r.date==S.day});
 var byd={};vis.forEach(function(r){(byd[r.date]=byd[r.date]||[]).push(r)});
 Object.keys(byd).sort().reverse().forEach(function(d){
  h+='<tr style="font-weight:600"><td style="background:#eef2ff">'+d+' 小计</td>';
  sl.forEach(function(s){var t=0,n=0;byd[d].forEach(function(r){var v=s.fvals[r.i];if(v!=null){t+=v;n++}});h+='<td style="background:#eef2ff" title="有数据的时段数 '+n+'">'+(n?f(t):"—")+'</td>'});h+='</tr>';
  byd[d].forEach(function(r){h+='<tr><td title="'+r.title+'">'+r.label+'</td>';sl.forEach(function(s){h+='<td>'+f(s.fvals[r.i])+'</td>'});h+='</tr>'})});
 T.innerHTML=h;
 // compare days for one seller
 var s=sl[S.seller],M={},dset={};
 rows.forEach(function(r){if(!r.cmp)return;var hr=new Date(r.r-3600000),d=hISO(r.r-3600000),hh=hr.getUTCHours();dset[d]=1;(M[d]=M[d]||{})[hh]=s.fvals[r.i]});
 var dl=Object.keys(dset).sort().reverse(),mx=0;
 dl.forEach(function(d){for(var k=0;k<24;k++){var v=M[d][k];if(v!=null&&v>mx)mx=v}});
 if(!dl.length){C.innerHTML='<tr><td class="muted">暂无间隔约1小时的有效时段。</td></tr>';return}
 var c='<tr><th>小时</th><th>平均</th>';dl.forEach(function(d){c+='<th>'+d.slice(5)+'</th>'});c+='</tr>';
 for(var k=0;k<24;k++){var sum=0,n=0;dl.forEach(function(d){var v=M[d][k];if(v!=null){sum+=v;n++}});
  c+='<tr><td>'+k+'点</td><td><b>'+(n?(Math.round(sum/n*10)/10):"—")+'</b></td>';
  dl.forEach(function(d){var v=M[d][k];c+='<td'+hCol(v,mx)+'>'+f(v)+'</td>'});c+='</tr>'}
 c+='<tr style="font-weight:600"><td style="background:#eef2ff">当日小计</td><td style="background:#eef2ff">—</td>';
 dl.forEach(function(d){var t=0,n=0;for(var k=0;k<24;k++){var v=M[d][k];if(v!=null){t+=v;n++}}c+='<td style="background:#eef2ff" title="有数据的小时数 '+n+'">'+(n?f(t):"—")+'<br><span class="muted" style="font-weight:400">'+n+'h</span></td>'});c+='</tr>';
 C.innerHTML=c}
