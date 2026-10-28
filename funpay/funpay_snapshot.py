#!/usr/bin/env python3
"""Hourly FunPay snapshot (public data only).
Counter = number of NEW buyer reviews in category 'App Store & iTunes' per seller (proxy for completed orders; see site notes).
Method per seller: read the seller's total review count (all categories) from the public reviews endpoint; if it grew by d since the
previous snapshot, read the newest d reviews and count those labelled 'App Store & iTunes'.
Appends to funpay_hourly_history.csv: ts,region,seller_id,seller,profile_url,total_reviews,apple_cum,apple_new,status
  apple_cum = Apple reviews counted since monitoring started (starts at 0 at the first snapshot of that seller), apple_new = increment since the previous row.
  status: base (first row) | ok | reset (total decreased -> rebaseline, no value) | partial (could not read all new reviews -> no value)
Missing fetches write no row; the next good row's apple_new then covers the whole gap (builder will not attribute it to a single hour).
Apple reviews are also logged to funpay_reviews_log.csv (ts,region,seller_id,detail,date_label).
Exit codes: 0 ok, 2 more than 5 sellers failed (rows already written are kept)."""
import os,sys,csv,json,datetime,time
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from fp_lib import *
HIST=os.path.join(D,'funpay_hourly_history.csv'); LOG=os.path.join(D,'funpay_reviews_log.csv')
HDR=['ts','region','seller_id','seller','profile_url','total_reviews','apple_cum','apple_new','status']
MAXPAGES=20
def tsnow():
    try:
        import zoneinfo; n=datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Shanghai'))
    except Exception: n=datetime.datetime.utcnow()+datetime.timedelta(hours=8)
    return n.strftime('%Y-%m-%dT%H:%M')
def main():
    sellers=json.load(open(os.path.join(D,'funpay_sellers.json'),encoding='utf-8'))
    prev={}
    if os.path.exists(HIST):
        for r in csv.DictReader(open(HIST,encoding='utf-8')): prev[r['seller_id']]=r   # last row wins
    ts=tsnow(); out=[]; log=[]; lines=[]; failed=0
    for s in sellers:
        uid=str(s['uid']); p=prev.get(uid)
        first=reviews_page(uid)
        if first is None or first[0] is None: failed+=1; lines.append(f"{s['name']}: 抓取失败（本次跳过）"); continue
        total,revs,cont=first; status='base'; new=None; cum=0
        if p:
            cum=int(p['apple_cum']); d=total-int(p['total_reviews'])
            if d<0: status='reset'
            elif d==0: status='ok'; new=0
            else:
                got=list(revs); pages=1
                while len(got)<d and cont and pages<MAXPAGES:
                    nx=reviews_page(uid,cont)
                    if nx is None: break
                    got+=nx[1]; cont=nx[2]; pages+=1
                if len(got)<d: status='partial'
                else:
                    newr=got[:d]; ap=[r for r in newr if is_apple(r[1])]
                    new=len(ap); status='ok'
                    for r in ap: log.append([ts,s['region'],uid,r[1],r[0]])
            if new is not None: cum+=new
        out.append([ts,s['region'],uid,s['name'],'https://funpay.com/en/users/%s/'%uid,total,cum,'' if new is None else new,status])
        lines.append(f"{s['name']} [{s['region']}]: 评价总数 {total}，苹果类新增 {'—' if new is None else new}（{status}）")
    new_f=not os.path.exists(HIST)
    with open(HIST,'a',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        if new_f: w.writerow(HDR)
        w.writerows(out)
    if log:
        nl=not os.path.exists(LOG)
        with open(LOG,'a',newline='',encoding='utf-8') as f:
            w=csv.writer(f)
            if nl: w.writerow(['ts','region','seller_id','detail','date_label'])
            w.writerows(log)
    print('时间(北京时间)',ts); print('\n'.join(lines))
    if failed>5: print('FETCH FAILED for %d sellers'%failed,file=sys.stderr); return 2
    return 0
if __name__=='__main__': sys.exit(main())
