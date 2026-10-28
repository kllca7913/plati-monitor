function fpRegion(){return region=="FU"?"US":"TR"}
function fpRender(){
 var R=fpRegion(),FP=DATA.funpay||{sellers:[],cols:[],prev:[],dates:[]},nm=R=="US"?"美国":"土耳其";
 var S=FP.sellers.filter(function(s){return s.region==R});
 document.getElementById("fp_first").textContent=FP.first_ts?FP.first_ts.replace("T"," "):"尚无";
 document.getElementById("fp_rule").textContent=(DATA.funpay_rule||"");
 document.getElementById("fp_ht").textContent="FunPay "+nm+"卡 · 一天中哪个小时订单最多（按北京时间，各卖家分开）";
 document.getElementById("fp_dt").textContent="FunPay "+nm+"卡 · 每天新增订单（近似）";
 // hour-of-day heatmap
 var h='<tr><th>卖家</th><th>最佳时段</th>';for(var i=0;i<24;i++)h+='<th>'+i+'点</th>';h+='</tr>';
 S.forEach(function(s){var mx=0,bi=-1;s.avg.forEach(function(v,i){if(v!=null&&v>mx){mx=v;bi=i}});
  h+='<tr><td><a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.seller)+'</a></td><td>'+(bi<0?'—':bi+':00–'+(bi+1)+':00')+'</td>';
  s.avg.forEach(function(v,i){if(v==null){h+='<td class="muted">—</td>';return}
   var a=mx>0?Math.max(0.06,v/mx):0.06,fg=a>0.55?'#fff':'#222';
   h+='<td style="background:rgba(37,99,235,'+a.toFixed(2)+');color:'+fg+'" title="'+i+'点：共'+s.hsum[i]+'单，观察'+s.hobs[i]+'小时">'+v.toFixed(1)+'</td>'});h+='</tr>'});
 document.getElementById("fp_hod").innerHTML=h;
 // daily
 var ds=FP.dates.slice().reverse();
 h='<tr><th>卖家</th>';ds.forEach(function(d){h+='<th>'+d.slice(5)+'</th>'});h+='</tr>';
 S.forEach(function(s){h+='<tr><td>'+esc(s.seller)+'</td>';ds.forEach(function(d){var e=s.daily[d];
  h+=e?'<td><b>'+e.new+(e.gap?'*':'')+'</b><br><span class="muted">'+Math.round(e.min/6)/10+'h</span></td>':'<td class="muted">—</td>'});h+='</tr>'});
 document.getElementById("fp_day").innerHTML=h;
 histMount("fp_hist","fp"+R,{fts:FP.fts||[],fprev:FP.fprev||[],sellers:S},"FunPay "+nm+"卡","funpay_hourly.csv")}
