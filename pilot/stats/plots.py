"""Summary plots for the confirmed papers (meta.json) against a random sample of scanned papers (baseline.json)."""
import json, collections, statistics as st
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/home/user/reviews/stats/'; c=json.load(open('meta.json')); b=json.load(open('baseline.json')); N=len(c)
BLUE='#2a78d6'; GREY='#a9a8a2'; INK='#0b0b0b'; SUB='#52514e'; SURF='#fcfcfb'
CAT=['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300']
plt.rcParams.update({'font.size':15,'font.family':'DejaVu Sans','axes.edgecolor':'#c9c8c2','axes.labelcolor':SUB,'xtick.color':SUB,'ytick.color':SUB,'text.color':INK,'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF})
def fig(title,sub,w=10,h=6.2):
    f,ax=plt.subplots(figsize=(w,h)); f.suptitle(title,x=0.02,y=0.98,ha='left',fontsize=20,fontweight='bold'); f.text(0.02,0.915,sub,ha='left',va='top',fontsize=13.5,color=SUB)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    ax.tick_params(length=0); return f,ax
def save(f,name,top=0.84): f.tight_layout(rect=(0,0,1,top)); f.savefig(OUT+name,dpi=170); plt.close(f); print('wrote',name)
def vbars(ax,labels,vals,color=BLUE,fmt=str):
    r=ax.bar(range(len(vals)),vals,color=color,width=0.72); ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels)
    for x,v in zip(range(len(vals)),vals): ax.text(x,v+max(vals)*0.015,fmt(v),ha='center',va='bottom',fontsize=14)
    ax.yaxis.grid(True,color='#e6e5e0',lw=1); ax.set_axisbelow(True); ax.spines['left'].set_visible(False)
def hbars(ax,labels,vals,color=BLUE,fmt=str):
    y=range(len(vals))[::-1]; ax.barh(list(y),vals,color=color,height=0.7); ax.set_yticks(list(y)); ax.set_yticklabels(labels)
    for yy,v in zip(y,vals): ax.text(v+max(vals)*0.012,yy,fmt(v),va='center',fontsize=14)
    ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.set_xlim(0,max(vals)*1.12)
# 1 citations
cit=[x['cited'] for x in c]; edges=[(0,0,'0'),(1,2,'1–2'),(3,5,'3–5'),(6,10,'6–10'),(11,20,'11–20'),(21,50,'21–50'),(51,10**6,'51+')]
f,ax=fig('Citations per paper',f'{N} papers with a confirmed duplicated image. Median {st.median(cit):g} citations, maximum {max(cit)}; {sum(cit):,} in total.\nCounts from Europe PMC, November 2026.')
vbars(ax,[e[2] for e in edges],[sum(lo<=v<=hi for v in cit) for lo,hi,_ in edges]); ax.set_xlabel('Times cited'); ax.set_ylabel('Papers'); save(f,'citations_histogram.png')
# 1b citations per year since publication
f,ax=fig('Citations per year since publication','Citations divided by years since the publication year (2026 papers count as one year).\nMore than half of the papers were published in 2024 or later.')
rate=[x['cited']/max(1,2026-x['year']) for x in c]; ed=[(0,0.001,'0'),(0.001,1,'up to 1'),(1,2,'1–2'),(2,4,'2–4'),(4,8,'4–8'),(8,1e9,'8+')]
vbars(ax,[e[2] for e in ed],[sum(lo<v<=hi if lo else v==0 for v in rate) for lo,hi,_ in ed]); ax.set_xlabel('Citations per year'); ax.set_ylabel('Papers'); save(f,'citations_per_year_histogram.png')
# 2 country pie
cc=collections.Counter(x['country'] for x in c); top=[k for k,_ in cc.most_common(6)]; other=N-sum(cc[k] for k in top)
f,ax=plt.subplots(figsize=(10,7)); f.suptitle('Country of the first author',x=0.02,y=0.98,ha='left',fontsize=20,fontweight='bold')
f.text(0.02,0.915,f'{N} papers with a confirmed duplicated image, from {len(cc)} countries.\n"Other" is {len(cc)-6} countries with one or two papers each.',ha='left',va='top',fontsize=13.5,color=SUB)
vals=[cc[k] for k in top]+[other]; labs=[f'{k}  {cc[k]} ({cc[k]/N:.0%})' for k in top]+[f'Other  {other} ({other/N:.0%})']
ax.pie(vals,labels=labs,colors=CAT+[GREY],startangle=90,counterclock=False,wedgeprops={'edgecolor':SURF,'linewidth':2},textprops={'fontsize':14},labeldistance=1.08)
ax.set_aspect('equal'); f.tight_layout(rect=(0,0,1,0.86)); f.savefig(OUT+'country_pie.png',dpi=170); plt.close(f); print('wrote country_pie.png')
# 2b countries bar (all with >=2) 
f,ax=fig('Country of the first author, all countries with two or more papers',f'{N} papers. Fourteen more countries have one paper each.',h=6.6)
two=[(k,v) for k,v in cc.most_common() if v>=2]; hbars(ax,[k for k,_ in two],[v for _,v in two]); save(f,'country_bar.png',top=0.88)
# 3 China share vs scanned pool
kinds={'Cell-assay image':'cell','Animal imaging scan':'bli_p'}; names={'cell':'Cell-assay scan','bli_p':'Animal-imaging scan'}
f,ax=fig('Share of papers from China','Confirmed papers against a random sample of about 300 papers from each scan.\nThe share among confirmed papers is no higher than among all scanned papers.',h=5.6)
rows=[]; 
for k,s in kinds.items():
    conf=[x for x in c if x['kind']==k]; base=[x for x in b if x['scan']==s and x['country']]
    rows.append((names[s],sum(x['country']=='China' for x in base)/len(base),len(base),sum(x['country']=='China' for x in conf)/len(conf),len(conf)))
import numpy as np
y=np.arange(len(rows))[::-1]; h=0.36
ax.barh(y+h/2+0.02,[r[1]*100 for r in rows],height=h,color=GREY,label='All scanned papers (sample)'); ax.barh(y-h/2-0.02,[r[3]*100 for r in rows],height=h,color=BLUE,label='Confirmed duplicated image')
for yy,r in zip(y,rows):
    ax.text(r[1]*100+1,yy+h/2+0.02,f'{r[1]:.0%}  (n = {r[2]})',va='center',fontsize=14); ax.text(r[3]*100+1,yy-h/2-0.02,f'{r[3]:.0%}  (n = {r[4]})',va='center',fontsize=14)
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.set_xlim(0,100); ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.set_xlim(0,118); ax.legend(frameon=False,loc='upper right',fontsize=13,bbox_to_anchor=(1.0,1.12),ncol=2); save(f,'china_share_vs_scanned.png',top=0.80)
# 4 years
yc=collections.Counter(x['year'] for x in c); ys=list(range(min(yc),max(yc)+1))
f,ax=fig('Publication year',f'{N} papers. The scanned collection is itself weighted towards recent years,\nso the rise is not evidence of a trend.')
vbars(ax,[str(v) for v in ys],[yc.get(v,0) for v in ys],fmt=lambda v:str(v) if v else ''); ax.set_ylabel('Papers'); ax.tick_params(axis='x',labelsize=12); save(f,'publication_year.png')
# 5 journals
jc=collections.Counter(x['journal'] for x in c); tj=[(k,v) for k,v in jc.most_common() if v>=2]
f,ax=fig('Journals with two or more of the papers',f'{N} papers in {len(jc)} journals; {sum(v==1 for v in jc.values())} journals have one paper each.',w=11,h=7.2)
FIX={'PloS one':'PLoS One','IScience':'iScience'}; short=lambda s:FIX.get(s.split(' : ')[0][:1].upper()+s.split(' : ')[0][1:],s.split(' : ')[0][:1].upper()+s.split(' : ')[0][1:]); hbars(ax,[short(k) for k,_ in tj],[v for _,v in tj]); save(f,'journals.png',top=0.90)
# 6 image type
kc=collections.Counter(x['kind'] for x in c); order=['Cell-assay image','Colony plate','Animal imaging scan','Flow cytometry plot']
lab={'Cell-assay image':'Cell-assay scan\n(scratch, transwell)','Colony plate':'Colony plates','Animal imaging scan':'Animal-imaging scan\n(bioluminescence)','Flow cytometry plot':'Flow cytometry plots'}
f,ax=fig('Which search found the paper',f'{N} papers. A paper found by two searches is counted once, under the first.',h=5.4); hbars(ax,[lab[k] for k in order],[kc[k] for k in order]); save(f,'found_by_search.png',top=0.84)
json.dump({'n':N,'median_cited':st.median(cit),'mean_cited':st.mean(cit),'zero':sum(v==0 for v in cit),'countries':cc.most_common(),'china_rows':rows,'years':sorted(yc.items()),'journals':tj,'kinds':kc,'baseline_median_cited':{s:st.median([x['cited'] for x in b if x['scan']==s]) for s in ('cell','bli_p')},'baseline_median_year':{s:st.median([x['year'] for x in b if x['scan']==s]) for s in ('cell','bli_p')},'conf_median_year':st.median([x['year'] for x in c])},open('summary.json','w'),default=str,indent=1)
