from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np, cv2, os, math

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'assets' / 'source-photo.png')  # Add your source portrait here before regenerating
OUT = str(ROOT)
os.makedirs(OUT, exist_ok=True)

# Crop a head-and-shoulders region from the supplied cinematic workspace photo.
im=Image.open(SRC).convert('RGB')
# The subject is centered slightly right; keep face, shoulders and a little context.
crop=im.crop((105,45,330,285))
arr=np.array(crop)
# GrabCut segmentation: rectangle includes the person while excluding most surrounding desk/UI.
h,w=arr.shape[:2]
mask=np.zeros((h,w),np.uint8)
bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
rect=(int(w*.16), int(h*.04), int(w*.72), int(h*.90))
try:
    cv2.grabCut(cv2.cvtColor(arr,cv2.COLOR_RGB2BGR), mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    fg=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype('uint8')
    # Keep largest connected foreground component, then soften/clean edges.
    n, labels, stats, cents=cv2.connectedComponentsWithStats(fg,8)
    if n>1:
        idx=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]); fg=(labels==idx).astype('uint8')*255
    fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    fg=cv2.GaussianBlur(fg,(3,3),0)
except Exception:
    fg=np.ones((h,w),np.uint8)*255

# Convert to a compact binary dither. Dots represent the portrait, not the original photo.
gray=Image.fromarray(arr).convert('L')
gray=ImageOps.autocontrast(gray, cutoff=1)
gray=ImageEnhance.Contrast(gray).enhance(1.3)
gray=gray.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=3))
size=(112,136)
gray=gray.resize(size, Image.Resampling.LANCZOS)
mask_im=Image.fromarray(fg).resize(size, Image.Resampling.LANCZOS)
a=np.asarray(gray).astype(float)
m=np.asarray(mask_im)>70
# Floyd-Steinberg error diffusion, serpentine scan.
q=np.zeros_like(a,dtype=np.uint8); work=a.copy()
for y in range(size[1]):
    xs=range(size[0]) if y%2==0 else range(size[0]-1,-1,-1)
    direction=1 if y%2==0 else -1
    for x in xs:
        old=work[y,x]; new=255 if old>=128 else 0
        q[y,x]=new; err=old-new
        nx=x+direction
        if 0<=nx<size[0]: work[y,nx]+=err*7/16
        if y+1<size[1]:
            if 0<=x-direction<size[0]: work[y+1,x-direction]+=err*3/16
            work[y+1,x]+=err*5/16
            if 0<=nx<size[0]: work[y+1,nx]+=err/16

# Dither dots, with mask edge suppression. Use dark pixels for light theme and light pixels for dark theme.
dots=[]
for y in range(size[1]):
    for x in range(size[0]):
        if m[y,x] and q[y,x]==0:
            # small deterministic jitter avoids a rigid lattice while preserving legibility
            jx=math.sin(x*12.9898+y*78.233)*0.34
            jy=math.sin(x*39.3467+y*11.135)*0.34
            dots.append((x*2.65+1.3+jx,y*2.65+1.3+jy))

# Generate SVGs with two independent visual layers: detailed portrait and logo sequence.
W,H=1180,610
portrait_x,portrait_y=38,112
portrait_scale=1.48
# fit grid approx 297x360

def logo_svg(kind, color):
    # Stylised logo marks; transitions are crossfades, not official trademark artwork.
    if kind=='react':
        return f'''<g fill="none" stroke="{color}" stroke-width="3.2" stroke-linecap="round"><ellipse cx="0" cy="0" rx="34" ry="13"/><ellipse cx="0" cy="0" rx="34" ry="13" transform="rotate(60)"/><ellipse cx="0" cy="0" rx="34" ry="13" transform="rotate(120)"/><circle cx="0" cy="0" r="4" fill="{color}" stroke="none"/></g>'''
    if kind=='next':
        return f'''<g fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round"><path d="M-26 25 V-25 L18 25 V-25"/><path d="M-36 -36 H36 V36 H-36 Z" stroke-width="1.5" opacity=".35"/></g>'''
    return f'''<g fill="none" stroke="{color}" stroke-width="3.2" stroke-linejoin="round"><path d="M0 -35 L31 -18 L31 18 L0 36 L-31 18 L-31 -18 Z"/><path d="M0 -35 V0 L31 -18 M0 0 L-31 -18 M0 0 V36 M0 0 L31 18"/></g>'''

for mode in ('dark','light'):
    dark=mode=='dark'
    bg='#0A101F' if dark else '#F4F1EA'
    panel='#111B2D' if dark else '#FFFFFF'
    ink='#F8FAFC' if dark else '#1E293B'
    muted='#94A3B8' if dark else '#64748B'
    accent='#22D3EE' if dark else '#0891B2'
    portrait='#A78BFA' if dark else '#7C3AED'
    green='#10B981'; red='#F87171'
    circles=[]
    for x,y in dots:
        cx=portrait_x+x*portrait_scale; cy=portrait_y+y*portrait_scale
        circles.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="1.12"/>')
    portrait_group=''.join(circles)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<title>Rexbiswas — Rishi Biswas, Full-Stack Developer</title>
<desc>Animated terminal-style GitHub profile banner with a dithered portrait and React, Next.js and Three.js logo sequence.</desc>
<rect width="1180" height="610" rx="22" fill="{bg}"/>
<rect x="8" y="8" width="1164" height="594" rx="18" fill="{panel}" stroke="{accent}" stroke-opacity=".55" stroke-width="1.5"/>
<path d="M8 58 H1172" stroke="{muted}" stroke-opacity=".35"/>
<circle cx="34" cy="33" r="6" fill="#F87171"/><circle cx="56" cy="33" r="6" fill="#FBBF24"/><circle cx="78" cy="33" r="6" fill="{green}"/>
<text x="105" y="39" fill="{muted}" font-family="ui-monospace,monospace" font-size="17">profile.sh --live</text>
<rect x="1045" y="18" width="92" height="29" rx="14" fill="{red}" fill-opacity=".15" stroke="{red}"/>
<circle cx="1061" cy="32" r="4" fill="{red}"><animate attributeName="opacity" values="1;.25;1" dur="1.3s" repeatCount="indefinite"/></circle>
<text x="1073" y="37" fill="{red}" font-family="ui-monospace,monospace" font-size="12" font-weight="700">LIVE</text>
<text x="38" y="91" fill="{accent}" font-family="ui-monospace,monospace" font-size="13" letter-spacing="2">VISUAL.MAP</text>
<rect x="26" y="104" width="414" height="450" rx="12" fill="{bg}" stroke="{muted}" stroke-opacity=".35"/>
<g fill="{portrait}" shape-rendering="crispEdges">{portrait_group}</g>
<text x="38" y="579" fill="{muted}" font-family="ui-monospace,monospace" font-size="11">PORTRAIT.DATA // DITHERED</text>
<text x="490" y="91" fill="{accent}" font-family="ui-monospace,monospace" font-size="13" letter-spacing="2">SYSTEM.INFO</text>
<rect x="968" y="72" width="168" height="34" rx="17" fill="{portrait}" fill-opacity=".16" stroke="{portrait}"/>
<text x="1052" y="94" text-anchor="middle" fill="{portrait}" font-family="ui-monospace,monospace" font-size="14" font-weight="700">@Rexbiswas</text>
'''
    rows=[('Subject','Rishi Biswas'),('Role','Full-Stack Developer'),('Origin','India'),('Education','Economics Honours'),('Status','Building | Learning | Shipping'),('ToolChain','VS Code | Git'),('Core.Lang','JavaScript | Python | C++'),('Core.Frontend','React | Next.js | Tailwind'),('Core.Backend','Node.js | Express | PHP'),('Core.Database','MongoDB | MySQL | SQLite'),('Core.Infra','Vercel | GitHub'),('Grid.Mail','rexbiswas1@gmail.com'),('Grid.Portfolio','portfolio-nu.vercel.app'),('Grid.LinkedIn','linkedin.com/in/rishi-biswas'),('Grid.GitHub','github.com/Rexbiswas')]
    y=145
    for label,value in rows:
        svg+=f'''<text x="490" y="{y}" fill="{muted}" font-family="ui-monospace,monospace" font-size="14">{label}</text>
<path d="M{max(585, 490+len(label)*8)} {y-4} H{min(850, 780)}" stroke="{muted}" stroke-opacity=".35" stroke-dasharray="2 5"/>
<text x="870" y="{y}" fill="{ink}" font-family="ui-monospace,monospace" font-size="14">{value}</text>'''
        y+=27
    # animated technology mark sequence in lower-right, with label
    svg+=f'''<path d="M490 555 H1138" stroke="{muted}" stroke-opacity=".35"/>
<text x="490" y="582" fill="{muted}" font-family="ui-monospace,monospace" font-size="12">STACK.MORPH</text>
<g transform="translate(940 557)">
<g opacity="1">{logo_svg('react',accent)}<animate attributeName="opacity" values="1;1;0;0;0;0;1" keyTimes="0;.18;.24;.30;.85;.92;1" dur="6s" repeatCount="indefinite"/></g>
<g opacity="0">{logo_svg('next',portrait)}<animate attributeName="opacity" values="0;0;1;1;0;0;0" keyTimes="0;.18;.24;.48;.54;.92;1" dur="6s" repeatCount="indefinite"/></g>
<g opacity="0">{logo_svg('three',green)}<animate attributeName="opacity" values="0;0;0;0;1;1;0" keyTimes="0;.48;.54;.60;.66;.92;1" dur="6s" repeatCount="indefinite"/></g>
</g>
<text x="1000" y="562" fill="{ink}" font-family="ui-monospace,monospace" font-size="12">REACT / NEXT / THREE</text>
</svg>'''
    path=os.path.join(OUT,f'{mode}.svg')
    open(path,'w',encoding='utf-8').write(svg)

# Save intermediate portrait mask/data for future tuning.
Image.fromarray(fg).save(os.path.join(OUT,'portrait-mask.png'))
Image.fromarray(q).save(os.path.join(OUT,'portrait-dither.png'))
print('dots',len(dots))
for f in os.listdir(OUT): print(f, os.path.getsize(os.path.join(OUT,f)))
