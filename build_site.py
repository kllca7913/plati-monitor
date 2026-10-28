#!/usr/bin/env python3
"""Builds docs/index.html (self-contained), docs/data.json, docs/report.csv from report_data.json/history.csv. No cross-seller totals."""
import json,os,shutil,subprocess,sys,datetime,csv,html
D=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(D,'docs'); os.makedirs(OUT,exist_ok=True)
subprocess.run([sys.executable,os.path.join(D,'build_report.py')],check=True,stdout=subprocess.DEVNULL)
data=json.load(open(os.path.join(D,'report_data.json'),encoding='utf-8'))
try:
    import zoneinfo; now=datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Shanghai'))
except Exception:
    now=datetime.datetime.utcnow()+datetime.timedelta(hours=8)
data['updated']=now.strftime('%Y-%m-%d %H:%M')+'（北京时间）'
# last snapshot time from history.csv
last=None
for r in csv.DictReader(open(os.path.join(D,'history.csv'),encoding='utf-8')): last=(r['date'],r['time'])
data['last_snapshot']=(last[0]+' '+last[1]) if last else ''

# ---- hourly data (from hourly_history.csv; independent of daily logic) ----
def build_hourly():
    P=os.path.join(D,'hourly_history.csv'); H={'cols':[],'sellers':[],'first_ts':None,'last_ts':None}
    rows=list(csv.DictReader(open(P,encoding='utf-8'))) if os.path.exists(P) else []
    if not rows: return H,[]
    rows.sort(key=lambda r:r['ts'])
    tss=sorted({r['ts'] for r in rows}); H['first_ts']=tss[0]; H['last_ts']=tss[-1]
    F=datetime.datetime.fromisoformat
    by={}
    for r in rows: by.setdefault((r['region'],r['seller_id']),{})[r['ts']]=r
    cols=tss[-25:][1:] if len(tss)>1 else []
    H['cols']=cols; H['prev']=[tss[tss.index(c)-1] for c in cols]
    csvrows=[]; order=[]
    for r in rows:
        k=(r['region'],r['seller_id'])
        if k not in order: order.append(k)
    cut=F(tss[-1])-datetime.timedelta(hours=24)
    for k in order:
        m=by[k]; vals=[];tot=0;cov=0;have=False;gaps=[]
        for i,t in enumerate(tss):
            if i==0: continue
            a=m.get(tss[i-1]); b=m.get(t); v=None; status='ok'
            if not a or not b: status='missing'
            elif int(a['listings_fetched'])<int(a['listings_expected']) or int(b['listings_fetched'])<int(b['listings_expected']): status='partial'
            else: v=int(b['cum_sales'])-int(a['cum_sales'])
            mins=int((F(t)-F(tss[i-1])).total_seconds()//60)
            csvrows.append([t,k[0],k[1],(b or a)['seller'],tss[i-1],mins,'' if v is None else v,b['cum_sales'] if b else '',status])
            if t in cols:
                vals.append(v)
                if v is not None and F(t)>cut: tot+=v;cov+=mins;have=True
        last=m.get(tss[-1]) or list(m.values())[-1]
        shop=next((s.get('shop_url') for s in data['sellers'] if s['region']==k[0] and str(s.get('seller_id',''))==k[1]),None) or next((s.get('shop_url') for s in data['sellers'] if s['region']==k[0] and s['seller']==last['seller']),None)
        H['sellers'].append({'region':k[0],'seller':last['seller'],'shop_url':shop,'vals':vals,'total24':tot if have else None,'covered_min':cov,'cum':int(last['cum_sales'])})
    return H,csvrows
hourly,hcsv=build_hourly()
data['hourly']=hourly
with open(os.path.join(OUT,'hourly.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['ts_end','region','seller_id','seller','ts_prev','elapsed_min','new_orders','cum_sales','status']); w.writerows(hcsv)
json.dump(data,open(os.path.join(OUT,'data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
shutil.copy(os.path.join(D,'report.csv'),os.path.join(OUT,'report.csv'))
TPL=r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plati 苹果礼品卡卖家每日销量监测</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;font-size:14px}
header{background:#1f2937;color:#fff;padding:16px 14px}h1{margin:0 0 6px;font-size:18px}header p{margin:2px 0;font-size:12px;color:#cbd5e1}
.tabs{display:flex;gap:8px;padding:12px 14px 0}.tab{flex:1;padding:10px 0;text-align:center;border-radius:8px;background:#e5e7eb;font-weight:600;cursor:pointer;border:0;font-size:14px}
.tab.on{background:#2563eb;color:#fff}.card{background:#fff;margin:12px 14px;border-radius:10px;padding:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
h2{font-size:15px;margin:0 0 10px}.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;min-width:max-content}th,td{padding:7px 8px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap}
th{background:#f9fafb;font-weight:600;font-size:12px}th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:#fff}th:first-child{background:#f9fafb}
a{color:#2563eb;text-decoration:none}.muted{color:#9ca3af}.bar{display:flex;align-items:center;margin:6px 0;font-size:12px}
.bar .n{width:96px;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar .t{flex:1;background:#f1f5f9;height:16px;border-radius:3px;margin:0 6px}
.bar .f{height:16px;background:#2563eb;border-radius:3px;min-width:1px}.bar .v{width:52px;flex:none;text-align:right}
.note{font-size:12px;color:#6b7280;line-height:1.7;padding:0 14px 24px}.note li{margin-bottom:4px}
</style></head><body>
<header><h1>Plati 苹果礼品卡卖家每日销量监测</h1>
<p>最后更新：<span id="upd"></span></p><p>最近一次采集：<span id="snap"></span></p>
<p>每天 20:00（北京时间）记录日统计；“每小时”页签每小时采集一次；各卖家分开统计，不做跨卖家合计。</p></header>
<div class="tabs"><button class="tab on" data-r="US">美国卡 前10卖家</button><button class="tab" data-r="TR">土耳其卡 前10卖家</button><button class="tab" data-r="H">每小时</button></div>
<div id="daily">
<div class="card"><h2 id="bt"></h2><div id="bars"></div></div>
<div class="card"><h2 id="tt"></h2><div class="scroll"><table id="tbl"></table></div>
<p class="muted" style="font-size:12px;margin:8px 0 0">表格可左右滑动；日期按新到旧排列。单元格“新增/累计”：上为当日新增订单，下为累计销量。</p></div>
</div>
<div id="hourly" style="display:none">
<div class="card"><h2>每小时新增订单（近似）· 近24小时合计</h2><div class="sub" style="font-size:12px;color:#6b7280;margin-bottom:8px">先看美国/土耳其分区，各卖家分开，不做跨卖家合计。</div><div id="hbars"></div></div>
<div class="card"><h2>每小时明细（北京时间，列标签为该时段结束时刻）</h2><div class="scroll"><table id="htbl"></table></div>
<p class="muted" style="font-size:12px;margin:8px 0 0">可左右滑动，新到旧排列。“—”表示该时段暂无数据（尚无上一次快照，或当次/上次有商品未取到，为避免误差不计算）。若两次快照间隔明显不是1小时，列标签带“*”。</p></div>
<ul class="note"><li><b>每小时数据（近似值）：</b>每小时采集一次各卖家商品的“累计已售”计数器（同样按卖家合并所有面额），每小时新增 = 相邻两次快照的累计之差。</li>
<li>每小时数据从首次每小时快照（<span id="hfirst"></span>）开始，之前没有数据；每小时采集与每晚 20:00 的日统计互相独立，两者数字可能不完全一致。</li>
<li>“24h合计”只对单个卖家，累加最近24小时内有数据的时段，并标注已覆盖的小时数；不同卖家之间不求和。</li></ul></div>
<ul class="note" id="dnote"><li><b>数据说明（近似值）：</b>数据来自 Plati 公开搜索接口中各商品的“累计已售”计数器，对每个卖家下固定的苹果礼品卡商品，按卖家合并所有面额后求和。</li>
<li>每日新增订单 = 当晚 20:00 快照与上一日快照的累计销量之差，并非卖家后台的真实订单数。</li>
<li>若某商品当次搜索未被返回，则不会计入该卖家，数字可能略偏低；“—”表示当天无对比数据（首日基线或缺数据）。</li>
<li>各卖家之间不求和；美国卡与土耳其卡分开统计，同一卖家可能同时出现在两个榜单中（分别统计各自的商品）。</li></ul>
<script>
var DATA=__DATA__;
var dates=DATA.dates.slice().reverse(),region="US";
function hl(t,p){var d=t.slice(5,10),h=t.slice(11,16),g=(new Date(t+":00Z")-new Date(p+":00Z"))/60000;return d+"<br>"+h+((g<45||g>75)?"*":"")}
function renderH(){var H=DATA.hourly,cols=H.cols.slice(),rc=cols.slice().reverse();
 document.getElementById("hfirst").textContent=H.first_ts?H.first_ts.replace("T"," "):"尚无";
 var S=H.sellers,b="";
 ["US","TR"].forEach(function(r){b+='<div style="font-weight:600;margin:10px 0 2px">'+(r=="US"?"美国卡":"土耳其卡")+'</div>';
  var L=S.filter(function(s){return s.region==r}),mx=1;L.forEach(function(s){if(s.total24>mx)mx=s.total24});
  L.forEach(function(s){var v=s.total24,w=v==null?0:Math.max(0,v)/mx*100,hrs=Math.round(s.covered_min/6)/10;
   b+='<div class="bar"><span class="n">'+esc(s.seller)+'</span><span class="t"><div class="f" style="width:'+w+'%"></div></span><span class="v" style="width:92px">'+(v==null?"—":f(v)+' <span class="muted">/'+hrs+'h</span>')+'</span></div>'})});
 document.getElementById("hbars").innerHTML=b+(cols.length?'':'<p class="muted" style="font-size:12px">目前只有首次快照作为基线，下一次每小时快照后开始显示新增订单。</p>');
 var h='<tr><th>卖家</th><th>24h合计</th>';rc.forEach(function(t){var i=cols.indexOf(t);h+='<th>'+hl(t,H.prev[i])+'</th>'});h+='</tr>';
 ["US","TR"].forEach(function(r){h+='<tr><td colspan="'+(2+rc.length)+'" style="background:#eef2ff;font-weight:600">'+(r=="US"?"美国卡":"土耳其卡")+'</td></tr>';
  S.filter(function(s){return s.region==r}).forEach(function(s){h+='<tr><td>'+esc(s.seller)+'</td><td><b>'+f(s.total24)+'</b></td>';
   rc.forEach(function(t){var i=cols.indexOf(t);h+='<td>'+f(s.vals[i])+'</td>'});h+='</tr>'})});
 document.getElementById("htbl").innerHTML=h}
function show(){var H=region=="H";document.getElementById("daily").style.display=H?"none":"";document.getElementById("dnote").style.display=H?"none":"";document.getElementById("hourly").style.display=H?"":"none";if(H)renderH();else render()}
function f(n){return n==null?"—":String(n).replace(/\B(?=(\d{3})+(?!\d))/g,",")}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function render(){
 var S=DATA.sellers.filter(function(s){return s.region==region});
 var name=region=="US"?"美国":"土耳其",ld=DATA.dates[DATA.dates.length-1];
 document.getElementById("tt").textContent=name+"苹果礼品卡 · 各卖家销量";
 document.getElementById("bt").textContent=name+"卡 · "+ld+" 各卖家新增订单（近似）";
 var mx=1;S.forEach(function(s){if(s.new[ld]>mx)mx=s.new[ld]});
 var b="";S.forEach(function(s){var v=s.new[ld];var w=v==null?0:Math.max(0,v)/mx*100;
  b+='<div class="bar"><span class="n">'+esc(s.seller)+'</span><span class="t"><div class="f" style="width:'+w+'%"></div></span><span class="v">'+(v==null?"—":f(v))+'</span></div>'});
 document.getElementById("bars").innerHTML=b+(S.every(function(s){return s.new[ld]==null})?'<p class="muted" style="font-size:12px">首日为基线，次日起显示新增订单。</p>':'');
 var h='<tr><th>卖家</th><th>商品数</th>';dates.forEach(function(d){h+='<th>'+d.slice(5)+'<br>新增 / 累计</th>'});h+='</tr>';
 S.forEach(function(s){h+='<tr><td>'+(s.shop_url?'<a href="'+esc(s.shop_url)+'" target="_blank" rel="noopener">'+esc(s.seller)+'</a>':esc(s.seller))+'</td><td>'+s.n_listings+'</td>';
  dates.forEach(function(d){h+='<td><b>'+f(s.new[d])+'</b><br><span class="muted">'+f(s.cum[d])+'</span></td>'});h+='</tr>'});
 document.getElementById("tbl").innerHTML=h;
}
document.getElementById("upd").textContent=DATA.updated;document.getElementById("snap").textContent=DATA.last_snapshot;
Array.prototype.forEach.call(document.querySelectorAll(".tab"),function(t){t.onclick=function(){region=t.getAttribute("data-r");
 Array.prototype.forEach.call(document.querySelectorAll(".tab"),function(x){x.classList.toggle("on",x===t)});show()}});
show();
</script></body></html>'''
js=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(TPL.replace('__DATA__',js))
print('built',os.path.join(OUT,'index.html'))
