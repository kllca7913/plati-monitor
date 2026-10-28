import sys,json,collections,concurrent.futures as cf
sys.path.insert(0,'.')
from fp_lib import *
S=lot_sellers(); print(len(S),'sellers')
def f(u):
    revs=[];c='';tot=None
    for _ in range(4):
        r=reviews_page(u,urllib.parse.quote(c) if False else c)
        if r is None: break
        tot,rv,c=r; revs+=rv
        if not c: break
    return u,tot,revs
out={}
with cf.ThreadPoolExecutor(5) as ex:
    for u,tot,revs in ex.map(f,[u for u in S if S[u]['try'] or S[u]['usd']]):
        out[u]={'tot':tot,'n':len(revs),'apple':sum(is_apple(r[1]) for r in revs),'labels':dict(collections.Counter(r[0] for r in revs)),
                'apple_labels':dict(collections.Counter(r[0] for r in revs if is_apple(r[1]))),**S[u]}
json.dump(out,open('survey.json','w'),ensure_ascii=False,indent=1)
