"""Local educational garment modules; no model-generated coordinates."""
from drafting import draft_front_bodice,draft_back_bodice,draft_sleeve,draft_sash
from ai_drafting import validate_draft
OPTIONS={'neckline':['square','round','v'], 'collar':['none','notched','flat'], 'closure':['back_zip','front_buttons'], 'sleeve':['none','short','puff','long'], 'cuffs':[False,True], 'skirt':['straight','flared','gathered'], 'sash':[False,True]}
def build(spec,m):
    for k,opts in OPTIONS.items():
        if k not in spec or spec[k] not in opts: raise ValueError('Unsupported or missing design option: '+k)
    if spec.get('unsupported'): raise ValueError('Unsupported design details: '+str(spec['unsupported'])[:300])
    if spec['collar']=='notched' and (spec['closure']!='front_buttons' or spec['neckline']!='v'): raise ValueError('Notched collar requires V neckline and front buttons in this prototype.')
    if spec['cuffs'] and spec['sleeve']=='none': raise ValueError('Cuffs require sleeves.')
    pieces=[]; notes=['Review all seams and make a toile. Internal darts and precise collar roll are not drafted.']
    def add(name,pts,q=2,fold=False,edges=None,grain='vertical'):
        pieces.append(dict(name=name,points=pts,quantity=q,fold=fold,grain=grain,edges=edges or ['seam']*(len(pts)-1)+['fold' if fold else 'seam']))
    def rect(name,w,h,q=2,grain='vertical'): add(name,[(0,0),(w,0),(w,h),(0,h)],q,grain=grain)
    front=spec['closure']=='front_buttons'; neck='square' if spec['neckline']=='square' else 'shallow'
    for isfront,p in [(True,draft_front_bodice(m,neck)),(False,draft_back_bodice(m,neck))]:
        pts=list(p['outline']); edges=list(p['kinds']); fold=isfront and not front
        if isfront and spec['neckline']=='v':
            n=p['labels'].index('N'); pts=[(0,min(18,m['front_length']*.45))]+pts[n:]; edges=['seam']+edges[n:]
        if isfront and front:
            # Separate placket, no overlap built into bodice.
            fold=False
        edges[-1]='fold' if fold else 'seam'
        add(('Front' if isfront else 'Back')+' bodice',pts,1 if fold else 2,fold,edges)
    length=m['dress_length']-m['front_length']; w=m['waist']/4+.5; hip=m['hip']/4+1
    if length<10: raise ValueError('Skirt length must be at least 10 cm.')
    top=w*(1.6 if spec['skirt']=='gathered' else 1); hem=max(top,hip)+(12 if spec['skirt']!='straight' else 0)
    # Hip shaping at a defined hip level; no implied straight-line fit.
    for name,fold in [('Front skirt',not front),('Back skirt',False)]:
        pts=[(0,0),(top,0),(max(top,hip),min(18,length/2)),(hem,length),(0,length)]
        add(name,pts,1 if fold else 2,fold,['seam','seam','seam','hem','fold' if fold else 'seam'])
    if front: rect('Centre-front placket',4,m['dress_length'],2); notes.append('Fit plackets to actual front opening; mark button positions after fitting.')
    if spec['collar']!='none':
        nw=m['bust']/12+.5; cw=max(8,nw*1.8)
        add('Collar prototype',[(0,0),(cw,0),(cw+2,6),(2,5)],2)
        rect('Front facing prototype',6,min(25,m['front_length']),2)
        notes.append('Collar and facing are rough blocks, not seam-matched lapel shapes. Redraft against the assembled neckline.')
    if spec['sleeve']!='none':
        p=draft_sleeve(m,1.5 if spec['sleeve']=='puff' else 1.0); pts=list(p['outline']); edges=list(p['kinds'])
        if spec['sleeve']=='long': pts=[(x,y+25 if y>p['dims']['cap_height']+1 else y) for x,y in pts]
        if spec['cuffs']: edges=['seam' if e=='hem' else e for e in edges]
        add(spec['sleeve'].title()+' sleeve',pts,2,False,edges)
        if spec['cuffs']: rect('Cuff prototype',m['upper_arm']+2,6,2); notes.append('Measure actual cuff circumference before cutting; gather sleeve to cuff.')
    if spec['sash']: rect('Sash',m['waist']*2,10,2,'horizontal')
    return validate_draft(dict(design=str(spec.get('description','Image-inspired dress')),assumptions=[str(spec.get('assumptions','Hidden construction unknown'))],sewing=notes+['Join bodice shoulders and sides; assemble skirt and join waist; attach sleeves and closure as applicable.'],pieces=pieces),m['seam_allowance'])
