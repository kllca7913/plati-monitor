#!/usr/bin/env python3
"""Hourly snapshot of cumulative numsold per seller (merged over all listings of the seller within a region).
Appends per-seller rows to hourly_history.csv (ts,region,seller_id,seller,cum_sales,listings_fetched,listings_expected).
Does NOT touch history.csv (daily logic). Never sums across sellers.
A row is 'partial' if listings_fetched < listings_expected; diffs are never computed from/against a partial row.
Exit codes: 0 ok, 2 fetch failed (nothing appended)."""
import json,subprocess,csv,os,datetime,time,urllib.parse,sys
D=os.path.dirname(os.path.abspath(__file__))
REG={'TR':json.load(open(os.path.join(D,'listings.json'))),'US':json.load(open(os.path.join(D,'listings_us.json')))}
ORDER={'TR':[316903,1288852,1091690,27402,1062128,1079090,325919,1060044,1033953,1123864],
       'US':[97839,316903,180983,315421,27402,1288852,808751,172340,325919,1419853]}
TITLE={'TR':'土耳其苹果礼品卡 (TR)','US':'美国苹果礼品卡 (US)'}
QS=[('itunes турция',1),('app store турция',1),('apple турция',1),('apple gift card',4),
    ('apple gift card usa',1),('itunes usa',1),('apple сша',1),('app store сша',1),('itunes сша',1),('apple usa',1),('apple gift card us',1),('itunes gift card usd',1)]
HDR=['ts','region','seller_id','seller','cum_sales','listings_fetched','listings_expected']
HIST=os.path.join(D,'hourly_history.csv')
def get(q,p):
    u='https://plati.io/api/search.ashx?query=%s&pagesize=500&pagenum=%d&visibleOnly=true&response=json'%(urllib.parse.quote(q),p)
    for _ in range(3):
        r=subprocess.run(['curl','-s','-m','60','-A','Mozilla/5.0',u],capture_output=True,text=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(3)
    return None
def tsnow():
    try:
        import zoneinfo; n=datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Shanghai'))
    except Exception: n=datetime.datetime.utcnow()+datetime.timedelta(hours=8)
    return n.strftime('%Y-%m-%dT%H:%M')
def main():
    allsold={};failed=0
    for q,pages in QS:
        for p in range(1,pages+1):
            d=get(q,p)
            if d is None: failed+=1; continue
            for x in d.get('items',[]): allsold[str(x['id'])]=int(x.get('numsold') or 0)
    if failed or not allsold:
        print('FETCH FAILED: %d query pages failed, %d listings seen'%(failed,len(allsold)),file=sys.stderr); return 2
    ts=tsnow()
    prev={}
    if os.path.exists(HIST):
        for r in csv.DictReader(open(HIST,encoding='utf-8')): prev[(r['region'],r['seller_id'])]=r   # last row wins (chronological append)
    out=[];lines=[]
    for reg in ('TR','US'):
        L=REG[reg]; lines.append('==== %s ===='%TITLE[reg])
        for sid in ORDER[reg]:
            ids=[i for i in L if L[i]['seller_id']==sid]
            got=[i for i in ids if i in allsold]
            name=L[ids[0]]['seller']; cum=sum(allsold[i] for i in got)
            out.append([ts,reg,sid,name,cum,len(got),len(ids)])
            p=prev.get((reg,str(sid)))
            if not p: lines.append(f'{name}: 累计 {cum}（首次记录，{len(got)}/{len(ids)} 个商品）'); continue
            el=datetime.datetime.fromisoformat(ts)-datetime.datetime.fromisoformat(p['ts']); mins=int(el.total_seconds()//60)
            et=f'{mins//60}小时{mins%60}分' if mins>=60 else f'{mins}分钟'
            if len(got)<len(ids) or int(p['listings_fetched'])<int(p['listings_expected']):
                lines.append(f'{name}: 累计 {cum}（部分数据 {len(got)}/{len(ids)}，本时段不计算新增；距上次 {et}）')
            else:
                lines.append(f'{name}: 距上次 {et} 新增 {cum-int(p["cum_sales"])} 单（累计 {cum}）')
    new=not os.path.exists(HIST)
    with open(HIST,'a',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        if new: w.writerow(HDR)
        w.writerows(out)
    print('时间(北京时间)',ts); print('\n'.join(lines)); return 0
if __name__=='__main__': sys.exit(main())
