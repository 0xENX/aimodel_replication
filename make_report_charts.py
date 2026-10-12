"""Regenerate the data behind every chart of the report and its Technical Annex.

Usage:  python make_report_charts.py   (after run_all.py, which writes outputs/sobol.json)
Writes outputs/charts/*.csv (large charts) and outputs/charts/inline.json (small charts).
"""
import sys, numpy as np, json, csv
import os
root=os.path.dirname(os.path.abspath(__file__)); out=os.path.join(root,"outputs","charts"); os.makedirs(out,exist_ok=True); sys.path.insert(0,root)
from aimodel.analysis.montecarlo import run_mc
from aimodel.analysis.policy import evaluate
from aimodel.calibration.data import CAL
p,base,ai,m=run_mc(4000)
b=m['b50_2036'];ua=m['unemp_adv_2036']
A=b>=0;C=(b<=-2)|(ua>=3);B=~A&~C;S={'A':A,'B':B,'C':C,'All':np.ones_like(A)}
popw=CAL['pop_share']
def world(o):
    Y=o['Y'].sum(2); LS=(o['pop']*popw).sum(2); E=(o['pop']*(1-o['unemp'])*popw).sum(2); D=(o['ldem']*popw).sum(2)
    return dict(gdp=Y,lsupply=LS,ldemand=D,u=1-E/LS,profit=(o['profit_share']*o['Y']).sum(2)/Y,b50=o['Cg'][:,:,:,0].sum(2)/LS)
wa,wb=world(ai),world(base); yrs=range(0,21,2); md=lambda x,s: float(np.median(x[s]))
def W(name,rows,fields):
    with open(f'{out}/{name}.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(fields); [w.writerow([r[k] for k in fields]) for r in rows]
# 1 six-indicators
rows=[]
for sc in 'ABC':
  for ind in ['gdp','profit','ldemand','lsupply','b50','stress']:
    for t in yrs:
        if ind=='stress': v=md((wa['u'][t]-wb['u'][t])*100,S[sc])
        elif ind=='lsupply': v=0.0
        else: v=md((wa[ind][t]/wb[ind][t]-1)*100,S[sc])
        rows.append(dict(ind=ind,sc=sc,y=2026+t,v=round(v,2)))
W('six_indicators',rows,['ind','sc','y','v'])
# 2/3 aggregate levels (B line, A-C range) and no-AI
def lvl(o,k,t,s): return md((o['u'][t]/o['u'][0] if k=='stress' else (o[k][t]/o['lsupply'][0] if k=='ldemand' else o[k][t]/o[k][0]))*100,s)
for nm,src in [('aggregate_ai',wa),('aggregate_noai',wb)]:
    rows=[]
    for ind in ['gdp','b50','lsupply','ldemand','stress','profit']:
        for t in yrs:
            if nm=='aggregate_ai':
                vs=[lvl(src,ind,t,S[s]) for s in 'ABC']; v=vs[1]; lo,hi=min(vs),max(vs)
            else:
                v=lvl(src,ind,t,S['All']); lo=hi=v
            rows.append(dict(ind=ind,y=2026+t,v=round(v,1),lo=round(lo,1),hi=round(hi,1)))
    W(nm,rows,['ind','y','v','lo','hi'])
# 4 snapshot 2036 (inline)
snap=[]
for sc in ['A','B','C','All']:
    for ind in ['gdp','profit','ldemand','b50']: snap.append(dict(ind=ind,sc=sc,v=round(md((wa[ind][10]/wb[ind][10]-1)*100,S[sc]),2)))
    snap.append(dict(ind='ur_pp',sc=sc,v=round(md((wa['u'][10]-wb['u'][10])*100,S[sc]),2)))
shares={k:int(round(S[k].mean()*100)) for k in 'ABC'}
# 5 fan chart annex
rows=[]
series={'gdp':lambda t:(ai['Y'][t].sum(1)/base['Y'][t].sum(1)-1)*100,
 'labshare':lambda t:((ai['labshare'][t]*ai['Y'][t]).sum(1)/ai['Y'][t].sum(1)-(base['labshare'][t]*base['Y'][t]).sum(1)/base['Y'][t].sum(1))*100,
 'unemp_adv':lambda t:(ai['unemp'][t,:,0]-base['unemp'][t,:,0])*100,
 'b50':lambda t:None}
from aimodel.analysis.metrics import group_ratio
for ind,f in series.items():
    for t in range(21):
        x=group_ratio(ai,base,2026+t,0) if ind=='b50' else f(t)
        q=np.percentile(x,[5,25,50,75,95]); rows.append(dict(ind=ind,y=2026+t,**{k:round(float(v),2) for k,v in zip(['p5','p25','p50','p75','p95'],q)}))
W('fan_aggregate',rows,['ind','y','p5','p25','p50','p75','p95'])
# 6 labour market chart (new): ADV supply, demand with/without AI, unemployment gap band
rows=[]
LS0=ai['lsup'][0,:,0]; Da=ai['ldem'][:,:,0]; Db=base['ldem'][:,:,0]
for t in range(21):
    rows.append(dict(y=2026+t,supply=round(float(np.median(ai['lsup'][t,:,0]/LS0))*100,2),
      dem_noai=round(float(np.median(Db[t]/LS0))*100,2),dem_ai=round(float(np.median(Da[t]/LS0))*100,2),
      dem_ai_p5=round(float(np.percentile(Da[t]/LS0,5))*100,2),dem_ai_p95=round(float(np.percentile(Da[t]/LS0,95))*100,2)))
W('labour_adv',rows,['y','supply','dem_noai','dem_ai','dem_ai_p5','dem_ai_p95'])
# 7 groups
grp=[]
for key,rg,gn,mk in [('b50_world','World','Bottom 50%','b50'),('m40_world','World','Middle 40%','m40'),('t10_world','World','Top 10%','t10')]+[(f'{g}_{r}',R,G,f'{g}_{r}') for r,R in [('adv','Advanced'),('eme','Emerging'),('lic','Low-income')] for g,G in [('b50','Bottom 50%'),('m40','Middle 40%'),('t10','Top 10%')]]:
    x=m[f'{mk}_2036']; grp.append(dict(key=key,region=rg,group=gn,p5=round(float(np.percentile(x,5)),2),p50=round(float(np.median(x)),2),p95=round(float(np.percentile(x,95)),2),m46=round(float(np.median(m[f'{mk}_2046'])),2)))
# 8 sobol
s=json.load(open(f'{root}/outputs/sobol.json'))
names={'mid_adv':'Timing of adoption','psi':'New tasks per task displaced','theta':'Extent of automation','kappa':'Wage flexibility','lag_new':'Lag before new tasks','pi_save':'Cost saving on automated tasks','phi_s':'Substitutable share of exposure','k_slope':'Speed of adoption curve','rent_share':'Workers share of AI rents','mu':'Gain on augmented tasks','exp_mult':'Widening of exposure','beta_w':'Wage pass-through','eps':'Wage elasticity of labour demand'}
outs=['b50_2036','b50_2046','gdp_2036','unemp_adv_2036','debt_adv_2046']
order=sorted(names,key=lambda k:-max(s[o]['ST'][k] for o in outs))
sob=[dict(param=names[k],out=o,st=round(max(0.0,s[o]['ST'][k]),3)) for k in order for o in outs]
demand_max=max(s[o]['ST'][k] for o in s for k in ['eta','nu'])
# 9 policy
_,res=evaluate(2000)
short={'Status quo':'Status quo','Capital income tax +5 pp, recycled per head':'Capital income tax +5 pp, recycled','AI dividend fund (50% of AI-induced profits)':'AI dividend fund','Income support decoupled from work':'Income support decoupled from work','Retraining and new-task creation':'Retraining, faster new tasks','Bargaining and profit-sharing':'Bargaining, profit-sharing','Slower rollout (+2 years)':'Slower rollout (+2 years)','AI rents taxed where used':'AI rents taxed where used','Package: dividend + support + retraining + bargaining':'Package (4 measures)','Package + capital tax + rents taxed where used':'Package + capital tax + rents'}
pol=[]
for i,(nm,r) in enumerate(res.items()):
    x=r['mr']['b50_2036']; pol.append(dict(key=f'p{i}',name=short[nm],p5=round(float(np.percentile(x,5)),2),p50=round(float(np.median(x)),2),p95=round(float(np.percentile(x,95)),2),m46=round(float(np.median(r['mr']['b50_2046'])),2),pneg=round(float((x<0).mean()),2)))
json.dump(dict(snap=snap,shares=shares,grp=grp,sob=sob,pol=pol,demand_max=demand_max,
  never_short=float((ai['util'].min(axis=(0,2))>=1-1e-3).mean()*100)),open(f'{out}/inline.json','w'))
