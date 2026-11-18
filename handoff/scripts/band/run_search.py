import sys,json;sys.path.insert(0,'band')
from bandlib import *
import multiprocessing as mp
def f(it):
    try:
        g=load(it[1]);B,res=search_copies(g)
        return [it[0],len(B),[(round(r[0],4),round(r[1],3),r[2],r[3],r[4]) for r in res[:4]]]
    except Exception as e: return [it[0],-1,[]]
if __name__=='__main__':
    items=json.load(open(sys.argv[1]))
    with mp.Pool(3) as P: out=P.map(f,items,chunksize=8)
    json.dump(out,open(sys.argv[2],'w'))
