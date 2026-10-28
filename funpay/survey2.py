"""Deep survey: for each candidate seller read up to MAXP pages (25 reviews each, newest first) until the date label is no longer 'This month'.
Output survey2.json: apple reviews labelled 'This month' (Oct 1-28, 2026 at the time of run), total reviews labelled 'This month', censored flag if cap reached."""
import sys,json,concurrent.futures as cf
sys.path.insert(0,'.')
from fp_lib import *
MAXP=40
sv=json.load(open('survey.json'))
def f(u):
    c='';ap=0;tm=0;pages=0;censored=False;done=False;tot=None
    while pages<MAXP:
        r=reviews_page(u,c)
        if r is None: return u,None
        tot,rv,c=r; pages+=1
        for x in rv:
            if x[0]=='This month':
                tm+=1; ap+=is_apple(x[1])
            else: done=True
        if done or not c: break
    else: pass
    if not done and c: censored=True
    return u,{'apple_month':ap,'reviews_month':tm,'pages':pages,'censored':censored,'tot':tot}
with cf.ThreadPoolExecutor(5) as ex: res=dict(ex.map(f,[u for u in sv if sv[u]['apple']>=3 or sv[u]['n']<100]))
json.dump(res,open('survey2.json','w'))
print(len(res),'done',sum(1 for v in res.values() if v is None),'failed')
