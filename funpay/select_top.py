#!/usr/bin/env python3
"""One-off selection of the 20 tracked sellers (frozen afterwards in funpay_sellers.json). Inputs: survey.json, survey2.json (see survey.py / survey2.py).
Rule: candidates = sellers with offers in FunPay 'App Store & iTunes > Gift Cards' (https://funpay.com/en/lots/1316/) whose latest<=100 reviews contain >=3 Apple reviews (or who have <100 reviews).
Score = number of reviews in category 'App Store & iTunes' labelled 'This month' (Oct 1-28 2026), reading up to 1000 newest reviews (lower bound if capped).
Region: TR if >=60% of the seller's TRY+USD offers are TRY-denominated, US if >=60% are USD-denominated; sellers in between are excluded (their reviews cannot be attributed to one country).
Top 10 per region by score."""
import json
sv=json.load(open('survey.json')); s2=json.load(open('survey2.json')); sel=[]
for reg,key in (('TR','try'),('US','usd')):
    c=[]
    for u,v in s2.items():
        s=sv[u]
        if s[key]>=1 and s[key]/(s['try']+s['usd'])>=0.6: c.append((v['apple_month'],u,s,v))
    c.sort(key=lambda x:-x[0])
    for sc,u,s,v in c[:10]:
        sel.append(dict(uid=u,name=s['name'],region=reg,score_apple_reviews_this_month=sc,capped=v['censored'],tr_offers=s['try'],usd_offers=s['usd'],all_offers=s['all'],total_reviews_all_categories=s['tot']))
json.dump(sel,open('funpay_sellers.json','w'),ensure_ascii=False,indent=1)
for r in sel: print(r['region'],r['uid'],r['name'],r['score_apple_reviews_this_month'],'(capped)' if r['capped'] else '')
