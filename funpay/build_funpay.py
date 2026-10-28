#!/usr/bin/env python3
"""Reads funpay_hourly_history.csv -> dict for the site (and CSV exports). Never sums across sellers."""
import os,csv,json,datetime
D=os.path.dirname(os.path.abspath(__file__))
F=datetime.datetime.fromisoformat
def _round_hour(t):
    r=t.replace(minute=0,second=0,microsecond=0)
    return r+datetime.timedelta(hours=1) if t.minute>=30 else r
def build(outdir=None):
    P=os.path.join(D,'funpay_hourly_history.csv')
    out={'sellers':[],'cols':[],'prev':[],'dates':[],'first_ts':None,'last_ts':None,'nsnap':0}
    if not os.path.exists(P): return out
    rows=list(csv.DictReader(open(P,encoding='utf-8')))
    if not rows: return out
    rows.sort(key=lambda r:r['ts'])
    tss=sorted({r['ts'] for r in rows}); out['first_ts']=tss[0]; out['last_ts']=tss[-1]; out['nsnap']=len(tss)
    cols=tss[-25:][1:] if len(tss)>1 else []
    out['cols']=cols; out['prev']=[tss[tss.index(c)-1] for c in cols]
    by={};order=[]
    for r in rows:
        if r['seller_id'] not in by: by[r['seller_id']]=[]; order.append(r['seller_id'])
        by[r['seller_id']].append(r)
    alldates=set(); hourly_csv=[]; hod_csv=[]
    cut=F(tss[-1])-datetime.timedelta(hours=24)
    for uid in order:
        rs=by[uid]; last=rs[-1]; byts={r['ts']:r for r in rs}
        daily={}; hsum=[0]*24; hobs=[0]*24; tot24=0; cov24=0; have24=False
        for a,b in zip(rs,rs[1:]):
            if b['apple_new']=='' : continue
            n=int(b['apple_new']); mins=int((F(b['ts'])-F(a['ts'])).total_seconds()//60); d=a['ts'][:10]
            e=daily.setdefault(d,{'new':0,'min':0,'gap':False}); e['new']+=n; e['min']+=mins
            if mins>90: e['gap']=True
            if F(b['ts'])>cut: tot24+=n;cov24+=mins;have24=True
            if 45<=mins<=75:
                end=F(b['ts']); er=_round_hour(end)
                if abs((end-er).total_seconds())<=20*60:
                    h=(er.hour-1)%24; hsum[h]+=n; hobs[h]+=1
            hourly_csv.append([b['ts'],last['region'],uid,b['seller'],a['ts'],mins,n,b['apple_cum'],b['status']])
        alldates.update(daily)
        vals=[]
        for c,pv in zip(cols,out['prev']):
            b=byts.get(c); a=byts.get(pv)
            vals.append(int(b['apple_new']) if (a and b and b['apple_new']!='') else None)
        avg=[round(hsum[h]/hobs[h],2) if hobs[h] else None for h in range(24)]
        for h in range(24): hod_csv.append([last['region'],uid,last['seller'],h,hsum[h],hobs[h],'' if avg[h] is None else avg[h]])
        out['sellers'].append({'region':last['region'],'seller':last['seller'],'uid':uid,'url':last['profile_url'],'vals':vals,
            'total24':tot24 if have24 else None,'cov24':cov24,'daily':daily,'hsum':hsum,'hobs':hobs,'avg':avg,
            'cum':int(last['apple_cum']),'total_reviews':int(last['total_reviews'])})
    out['dates']=sorted(alldates)
    if outdir:
        os.makedirs(outdir,exist_ok=True)
        with open(os.path.join(outdir,'funpay_hourly.csv'),'w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['ts_end','region','seller_id','seller','ts_prev','elapsed_min','apple_reviews_new','apple_cum','status']); w.writerows(hourly_csv)
        with open(os.path.join(outdir,'funpay_hour_of_day.csv'),'w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['region','seller_id','seller','beijing_hour','sum_orders','hours_observed','avg_per_hour']); w.writerows(hod_csv)
    return out
if __name__=='__main__':
    o=build(); print(json.dumps(o,ensure_ascii=False)[:500])
