#!/usr/bin/env python3
"""One-off selection of the 20 tracked sellers (run once; result frozen in funpay_sellers.json).
Inputs: survey.json (per candidate seller: offers per currency in the Gift Cards lot https://funpay.com/en/lots/1316/, total reviews, Apple share of latest <=100 reviews)
        calib_A.json / calib_B.json (total review counts of all candidates at two times ~40 min apart)
Estimated Apple review rate = (d total reviews / d hours) x (Apple share of latest <=100 reviews).
Region eligibility: seller must have >=1 offer in the region currency (TRY for TR, USD for US) AND region offers >= REG_PURITY of ALL its offers in the lot
(sellers spread over many countries cannot be attributed to one region, since reviews do not state the country)."""
import json,sys
REG_PURITY=float(sys.argv[1]) if len(sys.argv)>1 else 0.5
sv=json.load(open('survey.json')); A=json.load(open('calib_A.json')); B=json.load(open('calib_B.json'))
rows=[]
for u,v in sv.items():
    if u not in A or u not in B or A[u][0] is None or B[u][0] is None: continue
    dh=(B[u][1]-A[u][1])/3600; d=B[u][0]-A[u][0]
    share=v['apple']/v['n'] if v['n'] else 0
    rows.append(dict(uid=u,name=v['name'],d=d,hours=round(dh,2),share=round(share,2),rate=round(d/dh*share,2),tot=v['tot'],
                     tr=v['try'],us=v['usd'],all=v['all'],ptr=v['try']/v['all'],pus=v['usd']/v['all']))
sel=[];used=set()
for reg,key,pk in (('TR','tr','ptr'),('US','us','pus')):
    c=[r for r in rows if r[key]>=1 and r[pk]>=REG_PURITY and r['uid'] not in used]
    c.sort(key=lambda r:-r['rate'])
    print('====',reg,len(c),'eligible')
    for i,r in enumerate(c[:14]): print(i+1,r['uid'],r['name'],'rate/h',r['rate'],'dTot',r['d'],'in',r['hours'],'h share',r['share'],'offers tr/us/all',r['tr'],r['us'],r['all'])
    for r in c[:10]: sel.append(dict(uid=r['uid'],name=r['name'],region=reg,est_rate_per_h=r['rate'],tr_offers=r['tr'],us_offers=r['us'],all_offers=r['all'])); used.add(r['uid'])
if '--write' in sys.argv: json.dump(sel,open('funpay_sellers.json','w'),ensure_ascii=False,indent=1); print('written',len(sel))
