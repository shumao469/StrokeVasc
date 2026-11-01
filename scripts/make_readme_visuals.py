"""Build documentation-only SVG illustrations from analytic curves.

Inputs: Python standard library and a fixed random seed.
Outputs: two SVGs in assets/readme. All geometry is procedural.
"""
from pathlib import Path
import html, math, random

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/readme'
PALETTE=['#42d3c0','#73b8ff','#ffb26b','#c2a4ff','#ef8ca9','#82d5ed','#d4c980']
# An illustrative vessel network, deliberately separate from anatomical case data.
CURVES=[
 ([(0,0),(-2,-25),(2,-52),(0,-82)],0,13),
 ([(0,-82),(-13,-104),(-40,-117),(-68,-119)],1,10),
 ([(0,-82),(13,-104),(40,-117),(68,-119)],2,10),
 ([(-68,-119),(-86,-106),(-90,-78),(-85,-51)],3,11),
 ([(68,-119),(86,-106),(90,-78),(85,-51)],4,11),
 ([(-85,-51),(-113,-53),(-147,-48),(-172,-35)],1,10),
 ([(85,-51),(113,-53),(147,-48),(172,-35)],2,10),
 ([(-85,-51),(-69,-28),(-37,-20),(-13,-18)],3,8),
 ([(85,-51),(69,-28),(37,-20),(13,-18)],4,8),
 ([(-13,-18),(-6,-16),(6,-16),(13,-18)],5,5),
 ([(-13,-18),(-21,9),(-20,32),(-13,60)],5,8),
 ([(13,-18),(21,9),(20,32),(13,60)],6,8),
 ([(-68,-119),(-52,-109),(-49,-84),(-58,-69)],0,4),
 ([(68,-119),(52,-109),(49,-84),(58,-69)],0,4),
 ([(-172,-35),(-194,-31),(-213,-9),(-224,13)],1,5),
 ([(172,-35),(194,-31),(213,-9),(224,13)],2,5),
 ([(-172,-35),(-186,-56),(-204,-64),(-227,-62)],1,4),
 ([(172,-35),(186,-56),(204,-64),(227,-62)],2,4),
]

def point(cp,t):
    a,b,c,d=cp;s=1-t
    return (s**3*a[0]+3*s*s*t*b[0]+3*s*t*t*c[0]+t**3*d[0],
            s**3*a[1]+3*s*s*t*b[1]+3*s*t*t*c[1]+t**3*d[1])

def network(cx,cy,scale=1,mode='tube',light=False):
    parts=[];rng=random.Random(20261102)
    def tr(p):return cx+p[0]*scale,cy+p[1]*scale
    for cp,idx,radius in CURVES:
        p=[tr(x) for x in cp];d=f'M {p[0][0]:.2f},{p[0][1]:.2f} C '+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in p[1:])
        col=PALETTE[idx] if mode!='gray' else '#92a5b7'
        if mode in ['tube','gray']:
            parts.append(f'<path d="{d}" stroke="{col}" stroke-width="{radius*scale:.2f}" fill="none" stroke-linecap="round" opacity=".95"/>')
            parts.append(f'<path d="{d}" stroke="white" stroke-width="{radius*scale*.2:.2f}" fill="none" stroke-linecap="round" opacity=".15"/>')
        else:
            for i in range(80):
                t=(i+.5)/80;x,y=point(cp,t)
                dt=.002;xn,yn=point(cp,min(1,t+dt));ang=math.atan2(yn-y,xn-x)
                for _ in range(3):
                    a=rng.uniform(0,2*math.pi);r=radius*.43
                    xx=x-math.sin(ang)*r*math.cos(a);yy=y+math.cos(ang)*r*math.cos(a)
                    xx,yy=tr((xx,yy))
                    parts.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="{rng.uniform(.65,1.15)*scale:.2f}" fill="{col}" opacity="{rng.uniform(.55,.95):.2f}"/>')
    return ''.join(parts)

def text(x,y,s,size=18,fill='#172e46',weight='400',extra=''):
    return f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" fill="{fill}" font-weight="{weight}" {extra}>{html.escape(s)}</text>'

def svg(w,h,body,label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(label)}"><title>{html.escape(label)}</title>{body}</svg>\n'

def banner():
    p=['<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#092335"/><stop offset="1" stop-color="#142e46"/></linearGradient><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#85b8ce" stroke-opacity=".08"/></pattern></defs>',
       '<rect width="1600" height="490" rx="24" fill="url(#bg)"/>',
       '<rect x="880" width="720" height="490" fill="url(#grid)"/>',
       '<circle cx="1240" cy="235" r="187" fill="#214357" opacity=".36"/>',
       '<rect x="64" y="51" width="236" height="32" rx="16" fill="#254658"/>',
       text(83,73,'StrokePointPlusPlus',17,'#beefea','700'),
       text(61,162,'StrokeVasc',68,'#ffffff','700'),
       text(64,208,'Cerebral artery labelling',29,'#d7e9f0','400'),
       text(64,248,'Geometry, anatomical identity and branch presence',22,'#a7c8d6'),
       '<rect x="64" y="283" width="665" height="1" fill="#648b9d" opacity=".45"/>',
       text(64,323,'PointNet++ features',20,'#61ddce','700'),
       text(292,323,'13 identities',20,'#b2d6ff','700'),
       text(467,323,'Streamlit explorer',20,'#ffca96','700'),
       text(64,393,'A reproducible toolbox for computational vascular anatomy',19,'#b9d0dc'),
       text(64,442,'Documentation illustration · procedural vascular geometry',14,'#92b0bf'),
       network(1232,302,1.12,'tube'),
       text(1007,56,'ANATOMICAL REPRESENTATIONS',15,'#a4c2d3','700'),
       '<rect x="1111" y="407" width="245" height="36" rx="18" fill="#244d5d"/>',
       text(1132,431,'Inspect · label · compare',17,'#c9f4ec','700')]
    return svg(1600,490,''.join(p),'StrokeVasc cerebral artery labelling toolbox with a procedural vascular illustration')

def representation():
    p=['<rect width="1600" height="650" rx="24" fill="#f3f7fa"/>',
       text(48,60,'From vascular geometry to named points',31,'#15344d','700'),
       text(48,94,'The same illustrative structure shown as foreground and coloured point representation',18,'#60778b'),
       '<rect x="40" y="123" width="740" height="426" rx="20" fill="white" stroke="#dbe5ec"/>',
       '<rect x="820" y="123" width="740" height="426" rx="20" fill="white" stroke="#dbe5ec"/>',
       text(70,165,'01  Supplied vessel foreground',20,'#28465e','700'),
       text(851,165,'02  Anatomical point representation',20,'#28465e','700'),
       network(410,400,1.12,'gray'),network(1190,400,1.12,'points'),
       '<path d="M781 334H818" stroke="#35677e" stroke-width="3"/><path d="m808 326 10 8-10 8" stroke="#35677e" stroke-width="3" fill="none"/>',
       text(69,514,'Physical coordinates provide a common spatial reference',17,'#60778b'),
       text(851,514,'Illustrative colours distinguish example arterial identities',17,'#60778b'),
       text(49,596,'Pointwise identity',18,'#15344d','700'),
       text(289,596,'Branch-presence evidence',18,'#15344d','700'),
       text(642,596,'Traceable label changes',18,'#15344d','700'),
       text(1030,596,'Interactive research viewer',18,'#15344d','700'),
       text(49,629,'Procedural documentation example. Coordinates and colours are constructed for illustration.',14,'#6b8092')]
    return svg(1600,650,''.join(p),'Procedural vessel foreground and anatomically coloured point-cloud illustration')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for name,content in [('strokevasc-banner.svg',banner()),('vessel-pointcloud-demo.svg',representation())]:
        (OUT/name).write_text(content,encoding='utf8',newline='\n')
        print('Created',str((OUT/name).relative_to(ROOT)))

if __name__=='__main__':main()
