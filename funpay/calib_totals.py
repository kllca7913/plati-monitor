"""Grab current total review counts of all candidate sellers -> calib_<tag>.json (used once for the top-10 selection)."""
import sys,json,time,concurrent.futures as cf
sys.path.insert(0,'.')
from fp_lib import *
tag=sys.argv[1]; sv=json.load(open('survey.json'))
def f(u):
    r=reviews_page(u); return u,(r[0] if r else None),time.time()
with cf.ThreadPoolExecutor(6) as ex: res=list(ex.map(f,sv))
json.dump({u:[t,ts] for u,t,ts in res},open('calib_%s.json'%tag,'w'))
print(tag,len(res),sum(1 for r in res if r[1] is None),'failed')
