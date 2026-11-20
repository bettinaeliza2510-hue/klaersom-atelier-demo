import io,math
from shapely.geometry import Polygon

def marker(pieces):
    rows=[]; area=0
    for p in pieces:
        poly=Polygon(p['cut_outline']); x,y,X,Y=poly.bounds; w,h=X-x,Y-y
        fold=p.get('fold','fold' in p['kinds']); q=p.get('quantity',1 if p['id']=='front_bodice' else 2)
        if fold: w*=2
        if p.get('grain')=='horizontal' or p['id']=='sash': w,h=h,w
        area+=poly.area*q*(2 if fold else 1); rows.extend([(w,h)]*q)
    def pack(items):
        shelves=[]
        for w,h in items:
            if w>150:return None
            for s in shelves:
                if s[0]+w<=150 and h<=s[1]:s[0]+=w;break
            else:shelves.append([w,h])
        return sum(s[1] for s in shelves)
    a,b=pack(rows),pack(sorted(rows,key=lambda r:-r[1]))
    if a is None:return 'Piece exceeds fabric width; wider fabric needed.'
    length=min(a,b); allocated=150*length/10000
    return f'Original order {a/100:.2f} m; improved {length/100:.2f} m; utilisation {area/10000/allocated*100:.1f}%; estimated allocated mass {allocated*.12:.2f} kg; scenario footprint {allocated*.12*29.1:.2f} kg CO2e (unverified emission factor).'

def tiled_pdf(pieces):
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    b=io.BytesIO(); c=canvas.Canvas(b,pagesize=A4); W,H=A4
    c.drawString(cm,H-2*cm,'Print at 100%. Verify 5 cm square before using.'); c.rect(cm,H-8*cm,5*cm,5*cm); c.showPage()
    for p in pieces:
        pts=p['cut_outline']; x,y,X,Y=Polygon(pts).bounds
        for r in range(math.ceil((Y-y)/25)):
            for j in range(math.ceil((X-x)/18)):
                c.setFont('Helvetica',9); c.drawString(cm,H-cm,f"{p['id']} | row {r+1}, column {j+1} | {p['cut']}")
                c.rect(cm,H-27*cm,18*cm,25*cm); c.saveState(); clip=c.beginPath(); clip.rect(cm,H-27*cm,18*cm,25*cm); c.clipPath(clip,stroke=0)
                for outline,dash in [(p['outline'],False),(pts,True)]:
                    c.setDash(4,3) if dash else c.setDash(); path=c.beginPath()
                    for i,(a,z) in enumerate(outline): (path.moveTo if i==0 else path.lineTo)(cm+(a-x-j*18)*cm,H-2*cm-(z-y-r*25)*cm)
                    path.close(); c.drawPath(path)
                c.restoreState(); c.drawString(cm,cm,'Trim frame and join edges. Use preview for markings. Fit unvalidated.'); c.showPage()
    c.save();return b.getvalue()
