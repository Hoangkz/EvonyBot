import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import math,sys
LIM=int(sys.argv[1])
views = [(1,'academy',(218,139)),(2,'hospital',(553,34)),(3,'stables',(780,-80)),(4,'barracks',(530,-160)),(5,'archer_camp',(798,-398)),
         (6,'workshop',(990,-290)),(7,'war_hall',(470,-555)),(8,'embassy',(131,-625)),(9,'market',(212,-370)),(10,'tavern',(25,-219)),(11,'forge',(-92,-496)),(12,'trap_factory',(-300,-360)),(13,'prison',(-512,-210))]
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
