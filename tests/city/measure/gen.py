import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import math,sys
LIM=int(sys.argv[1])
views = [(1,'academy',(385,84)),(2,'hospital',(665,-45)),(3,'stables',(849,-111)),(4,'barracks',(664,-217)),(5,'archer_camp',(974,-345)),
         (6,'workshop',(1131,-262)),(7,'war_hall',(345,-677)),(8,'embassy',(178,-715)),(9,'market',(238,-439)),(10,'tavern',(126,-271)),(11,'forge',(-8,-535)),(12,'trap_factory',(-239,-445)),(13,'prison',(-506,-248))]
rows=[]; prev=(0,0)
for plot,name,v in views:
    fx,fy=v[0]-prev[0],v[1]-prev[1]
    n=max(math.ceil(abs(fx)/LIM),math.ceil(abs(fy)/260),1)
    sx,sy=round(fx/n),round(fy/n)
    x1,y1=190-sx//2,340-sy//2
    rows.append(f"    {{'plot': {plot}, 'swipes': {[[[x1,y1],[x1+sx,y1+sy]]]*n}, 'view': {list(v)}, 'seen_21933': '{name}'}},")
    prev=v
p=f"bot/city/civ{CIV}/city_tour.py"
s=open(p,encoding='utf-8').read()
a=s.index('DATA = [')
open(p,'w',encoding='utf-8').write(s[:a]+"DATA = [\n"+"\n".join(rows)+"\n]\n")
