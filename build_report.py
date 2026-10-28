#!/usr/bin/env python3
"""Builds report.csv (wide) + report_data.json from history.csv. Daily new orders = per-seller sum over its listings of (latest snapshot of date D - latest snapshot of previous date); never summed across sellers."""
import csv,json,os,collections
D=os.path.dirname(os.path.abspath(__file__))
rows=list(csv.DictReader(open(os.path.join(D,'history.csv'))))
for r in rows: r['region']=r.get('region') or 'TR'
rows.sort(key=lambda r:(r['date'],r['time']))
snap={}  # (region,date,listing)->cum  (last = latest of the day)
meta={}
for r in rows:
    snap[(r['region'],r['date'],r['listing_id'])]=int(r['cum_sales']); meta[(r['region'],r['listing_id'])]=(int(r['seller_id']),r['seller'])
dates=sorted({r['date'] for r in rows})
shop={}
for r in csv.DictReader(open('/workspace/plati_turkey_top10.csv')): shop[int(r['seller_id'])]=r['shop_url']
for m in json.load(open(os.path.join(D,'sellers_meta.json'))): shop[m['seller_id']]=m['shop_url']
ORDER={'TR':[316903,1288852,1091690,27402,1062128,1079090,325919,1060044,1033953,1123864],'US':[97839,316903,180983,315421,27402,1288852,808751,172340,325919,1419853]}
out=[]
for reg in ('TR','US'):
    for sid in ORDER[reg]:
        ids=[i for (rg,i),(s,n) in meta.items() if rg==reg and s==sid]
        name=[n for (rg,i),(s,n) in meta.items() if rg==reg and s==sid][0]
        cum={};new={}
        for k,d in enumerate(dates):
            c=sum(snap.get((reg,d,i),0) for i in ids if (reg,d,i) in snap)
            if any((reg,d,i) in snap for i in ids): cum[d]=c
            if k>0 and d in cum and dates[k-1] in cum:
                pd=dates[k-1]
                new[d]=sum(snap[(reg,d,i)]-snap[(reg,pd,i)] for i in ids if (reg,d,i) in snap and (reg,pd,i) in snap)
        out.append(dict(seller=name,seller_id=sid,region=reg,shop_url=shop.get(sid,''),n_listings=len(ids),cum=cum,new=new))
json.dump({'dates':dates,'sellers':out},open(os.path.join(D,'report_data.json'),'w'),ensure_ascii=False,indent=1)
with open(os.path.join(D,'report.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['seller','region','shop_url','n_listings']+['new_orders_'+d for d in dates]+['cum_sales_'+d for d in dates])
    for s in out:
        w.writerow([s['seller'],s['region'],s['shop_url'],s['n_listings']]+[s['new'].get(d,'') for d in dates]+[s['cum'].get(d,'') for d in dates])
print(open(os.path.join(D,'report.csv'),encoding='utf-8-sig').read())
