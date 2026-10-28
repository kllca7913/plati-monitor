#!/usr/bin/env python3
"""FunPay helpers (public pages only, plain HTTP). Used by select_top.py and funpay_snapshot.py."""
import re,subprocess,html,time,urllib.parse
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
LOT_URL='https://funpay.com/en/lots/1316/'   # App Store & iTunes -> Gift Cards
APPLE='App Store & iTunes'
def curl(args,retries=3,timeout=40):
    for i in range(retries):
        r=subprocess.run(['curl','-s','-m',str(timeout),'-A',UA]+args,capture_output=True,text=True)
        if r.returncode==0 and r.stdout: return r.stdout
        time.sleep(2*(i+1))
    return None
def reviews_page(uid,cont=''):
    """POST users/reviews (the 'Show more reviews' AJAX of the public profile). Returns (total_reviews, [(date_label,detail,text)], next_token) or None."""
    t=curl(['-X','POST','https://funpay.com/en/users/reviews','-H','X-Requested-With: XMLHttpRequest',
            '--data-urlencode','user_id=%s'%uid,'--data-urlencode','continue=%s'%cont,'--data-urlencode','filter='])
    if t is None: return None
    revs=[]
    for b in t.split('review-container')[1:]:
        d=re.search(r'review-item-date">([^<]*)<',b); dt=re.search(r'review-item-detail">([^<]*)<',b); tx=re.search(r'review-item-text">\s*(.*?)\s*</div>',b,re.S)
        revs.append(((d.group(1).strip() if d else ''),(html.unescape(dt.group(1)).strip() if dt else ''),
                     (html.unescape(re.sub('<[^>]+>','',tx.group(1))).strip()[:60] if tx else '')))
    m=re.search(r'([\d\s\u00a0,]+)\s*reviews(?:\s+in\s+[^<]*)?<',t)
    total=int(re.sub(r'\D','',m.group(1))) if m and re.sub(r'\D','',m.group(1)) else (0 if not revs else None)
    c=re.search(r'name="continue" value="([^"]*)"',t)
    return total,revs,(c.group(1) if c else None)
def is_apple(detail): return detail.split(',')[0].strip()==APPLE
def lot_sellers():
    """Parse the Gift Cards lot page -> {uid:{name,rev,try,usd,all}} (offers per currency filter)."""
    h=curl([LOT_URL],timeout=90)
    if not h: return None
    S={}
    for b in re.split(r'(?=<a href="https://funpay.com/en/lots/offer\?id=)',h)[1:]:
        cur=re.search(r'data-f-currency="([^"]*)"',b); cur=cur.group(1) if cur else None
        u=re.search(r'users/(\d+)/',b)
        if not u: continue
        name=re.search(r'media-user-name">\s*([^<]*?)\s*</div>',b)
        rc=re.search(r'rating-mini-count">([^<]*)<',b); rc2=re.search(r'>(\d+) reviews<',b)
        rev=int(re.sub(r'\D','',(rc.group(1) if rc else '') or (rc2.group(1) if rc2 else '') or '0') or 0)
        s=S.setdefault(u.group(1),{'name':html.unescape(name.group(1)) if name else u.group(1),'rev':rev,'try':0,'usd':0,'all':0}); s['all']+=1
        if cur in('try','usd'): s[cur]+=1
    return S
