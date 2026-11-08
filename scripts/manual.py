#!/usr/bin/env python3
"""Rebuild the seven illustrated PDF guides using ReportLab and local app assets."""
from pathlib import Path
import sys, json, argparse, subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Build all seven illustrated guides, or one selected language.')
parser.add_argument('output',nargs='?')
parser.add_argument('--lang',choices=['nl','en','fr','de','es','it','pt'])
args=parser.parse_args()
if not args.lang and not args.output:
    for language in ('nl','en','fr','de','es','it','pt'):
        subprocess.run([sys.executable,__file__,'--lang',language],check=True)
    raise SystemExit(0)
LANG=args.lang or 'nl'
TOTAL_PAGES=9 if LANG in ('nl','en') else 5
VERSION=json.loads((ROOT/'package.json').read_text())['version']
OUT=Path(args.output) if args.output else ROOT/('Handleiding.pdf' if LANG=='nl' else 'User-Guide-'+LANG.upper()+'.pdf')
OUT.parent.mkdir(parents=True,exist_ok=True)
FONT=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf'),('Book','Georgia.ttf'),('BookBold','Georgia Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
GREEN=HexColor('#244437');GOLD=HexColor('#aa8040');INK=HexColor('#303d31');MUTED=HexColor('#6b7061');PAPER=HexColor('#f4efe2');LINE=HexColor('#d9d0ba')
W,H=595.276,841.89;M=48;CW=W-2*M
c=canvas.Canvas(str(OUT),pagesize=(W,H));c.setTitle(f'Tickertwister Desktop {VERSION} - '+('User Guide' if LANG=='en' else 'Gebruikershandleiding'));c.setAuthor('Bob Ceulemans');c.setSubject('Installation, financial screening and private research' if LANG=='en' else 'Installatie, financiële screening en persoonlijk onderzoeksdossier')
body=ParagraphStyle('body',fontName='Body',fontSize=10.5,leading=16,textColor=INK,spaceAfter=10)
bold=ParagraphStyle('bold',parent=body,fontName='Bold',fontSize=12,leading=17)
small=ParagraphStyle('small',parent=body,fontSize=8.5,leading=13,textColor=MUTED)
# ReportLab's markup bold family mapping.
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
y=0;page=0

def para(text,style=body,x=M,width=CW,gap=10):
    global y
    p=Paragraph(text,style);_,height=p.wrap(width,H)
    if y-height<76:raise ValueError(f'Page {page} overflows at {text[:70]}')
    p.drawOn(c,x,y-height);y-=height+gap

def heading(text):
    global y
    y-=7;para(text,bold,gap=8)

def box(title,text):
    global y
    p=Paragraph(text,body);_,h=p.wrap(CW-30,H);height=h+53
    if y-height<76:raise ValueError(f'Page {page} box overflows')
    c.setFillColor(HexColor('#e7eadc'));c.roundRect(M,y-height,CW,height,7,fill=1,stroke=0)
    c.setFillColor(GREEN);c.setFont('Bold',11);c.drawString(M+15,y-22,title)
    p.drawOn(c,M+15,y-36-h);y-=height+16

def start(title,kicker,subtitle=''):
    global y,page
    if page:c.showPage()
    page+=1;c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setStrokeColor(LINE);c.setLineWidth(.6);c.line(M,58,W-M,58)
    c.setFillColor(MUTED);c.setFont('Body',7.5);c.drawString(M,43,'Copyright ©2026 Bob Ceulemans');c.drawString(M,32,'All Rights Reserved.')
    c.drawRightString(W-M,43,f'Tickertwister Desktop · v{VERSION}');c.drawRightString(W-M,32,f'{page:02d} / {TOTAL_PAGES:02d}')
    c.drawImage(str(ROOT/'web/app-icon.png'),M,H-74,28,28,mask='auto')
    c.setFillColor(MUTED);c.setFont('Bold',8);c.drawString(M+34,H-61,'THE VALUE INVESTOR’S NOTEBOOK')
    c.setFillColor(GOLD);c.setFont('Bold',9);c.drawString(M,H-108,kicker.upper())
    y=H-129
    titleStyle=ParagraphStyle('title',fontName='Book',fontSize=29,leading=34,textColor=GREEN)
    para(title,titleStyle,gap=14)
    if subtitle:para(subtitle,ParagraphStyle('intro',parent=body,fontSize=12,leading=18,textColor=MUTED),gap=20)

def row(left,right):
    global y
    a=Paragraph(left,bold);b=Paragraph(right,body);_,ha=a.wrap(135,H);_,hb=b.wrap(CW-156,H);h=max(ha,hb)
    if y-h<76:raise ValueError('row overflow')
    a.drawOn(c,M,y-ha);b.drawOn(c,M+156,y-hb);y-=h+12;c.setStrokeColor(LINE);c.line(M,y+4,W-M,y+4);y-=9


if LANG in ('nl','en'):
    content=ROOT/'scripts'/'manuals'/f'{LANG}.py'
    exec(compile(content.read_text(),str(content),'exec'))
else:
    edition=json.loads((ROOT/'scripts/manuals/international.json').read_text())[LANG]
    c.setTitle(f'Tickertwister Desktop {VERSION} - '+edition['title'])
    start('Tickertwister<br/>Desktop',edition['title']+' · '+VERSION,edition['tagline'])
    img=ImageReader(str(ROOT/'web/buffett-munger.png'));iw,ih=img.getSize();height=355;width=height*iw/ih
    c.saveState();path=c.beginPath();path.roundRect(M,132,CW,355,10);c.clipPath(path,stroke=0);c.drawImage(img,M+(CW-width)/2,132,width,height,mask='auto');c.restoreState()
    c.setFillColor(GREEN);c.setFont('Body',11);c.drawString(M,111,edition['cover'])
    c.setFillColor(MUTED);c.setFont('Body',8.5);c.drawString(M,92,'Mac · 39 · ROE · ROA · FCFE · CAGR · AI-AIC')
    for index,(title,kicker,sections) in enumerate(edition['pages'],1):
        start(title,f'{index:02d} / '+kicker)
        for label,text in sections:
            heading(label);para(text)

c.save();print(OUT)
