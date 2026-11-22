import re
NORM={"people's republic of china":'China','pr china':'China','p.r. china':'China','p. r. china':'China','china':'China','usa':'United States','united states of america':'United States','united states':'United States','u.s.a':'United States','us':'United States','uk':'United Kingdom','united kingdom':'United Kingdom','england':'United Kingdom','scotland':'United Kingdom','wales':'United Kingdom','republic of korea':'South Korea','korea':'South Korea','south korea':'South Korea','taiwan':'Taiwan','roc':'Taiwan','r.o.c':'Taiwan','iran':'Iran','islamic republic of iran':'Iran','türkiye':'Turkey','turkey':'Turkey','the netherlands':'Netherlands','russian federation':'Russia','kingdom of saudi arabia':'Saudi Arabia','ksa':'Saudi Arabia','uae':'United Arab Emirates','brasil':'Brazil','españa':'Spain','deutschland':'Germany','czechia':'Czech Republic','viet nam':'Vietnam'}
KNOWN=set(NORM.values())|set('Japan Germany France Italy Spain India Canada Australia Brazil Egypt Poland Portugal Switzerland Sweden Denmark Norway Finland Belgium Austria Greece Israel Malaysia Thailand Singapore Pakistan Mexico Argentina Chile Netherlands Ireland Hungary Romania Vietnam Indonesia Iraq Jordan Lebanon Nigeria Russia New~Zealand Colombia Bangladesh Hong~Kong Qatar Kuwait Serbia Croatia Slovenia Tunisia Morocco Ghana Ethiopia Kenya Peru Cuba Ukraine Bulgaria Slovakia Lithuania Estonia Latvia Luxembourg Iceland Sri~Lanka Nepal Oman Philippines South~Africa Czech~Republic Saudi~Arabia Uruguay Cyprus Algeria Cameroon Uganda Tanzania Kazakhstan Macau'.replace('~','\x00').split())
KNOWN={k.replace('\x00',' ') for k in KNOWN}
CITY={'Shandong':'China','Weihai':'China','Beijing':'China','Shanghai':'China','Guangzhou':'China','Chengdu':'China','Wuhan':'China','Nanjing':'China','Hangzhou':'China','Tokyo':'Japan','Seoul':'South Korea','Boston':'United States','New York':'United States','California':'United States','Texas':'United States','London':'United Kingdom','State Key Laboratory':'China'}
STATES=r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b'
def country(a):
    if not a: return None
    a=re.sub(r'\S+@\S+','',a); a=re.sub(r'Electronic address:.*','',a).strip(' .;,')
    parts=[p.strip(' .') for p in a.split(',')]
    for p in reversed(parts[-3:]):
        q=re.sub(r'^\d[\d\- ]*|[\d\- ]*\d$','',p).strip(' .'); k=q.lower()
        if k in NORM: return NORM[k]
        if q in KNOWN: return q
        for n in sorted(KNOWN,key=len,reverse=True):
            if re.search(r'\b'+re.escape(n)+r'$',q): return n
        for kk,v in NORM.items():
            if len(kk)>3 and k.endswith(kk): return v
    for c,v in CITY.items():
        if c in a: return v
    if re.search(STATES+r'[ ,]*\d{5}',a) or re.search(STATES+r'$',parts[-1]): return 'United States'
    return None
def first_country(affs):
    for a in affs:
        c=country(a)
        if c: return c
    return None
