#!/usr/bin/env python3
"""Single-sheet external test circuit and matching wiring data, firmware 2.0.0.

Python + reportlab required. Optional --settings and --output select references
and destination; the shipped settings_reference.h makes this folder portable.
"""
from pathlib import Path
import argparse
import csv
import json
import re
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

HW = Path(__file__).resolve().parent
ROOT = HW.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--settings', type=Path)
parser.add_argument('--output', type=Path, default=ROOT / 'output/pdf')
args = parser.parse_args()
default_settings = ROOT / 'firmware/Otoskop/settings.h'
settings_path = args.settings or (default_settings if default_settings.exists() and
    'CHARGE_SENSE_GPIO' in default_settings.read_text() else HW / 'settings_reference.h')
settings = settings_path.read_text()
for name, value in {'LIGHT_GPIO':1, 'SHUTTER_GPIO':4, 'STATUS_GPIO':5,
                    'SD_CS':21, 'SD_SCK':7, 'SD_MISO':8, 'SD_MOSI':9,
                    'CHARGE_SENSE_GPIO':6, 'USB_SENSE_GPIO':2}.items():
    assert re.search(rf'\b{name}\s*=\s*{value}\b', settings), (name, value)

OUT = args.output.resolve(); OUT.mkdir(parents=True, exist_ok=True)
FONT = Path('/System/Library/Fonts/Supplemental')
if FONT.exists():
    for name, file in [('Arial','Arial.ttf'),('Arial-Bold','Arial Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(FONT/file)))
else:
    for name, file in [('Arial','DejaVuSans.ttf'),('Arial-Bold','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/dejavu/'+file))
W,H = landscape(A3)
INK,MUTED,GRID='#173047','#526779','#ccd8e1'
RED,BLUE,GREEN,AMBER='#b6323c','#146b9a','#187259','#946313'
PALE='#f4f7fa'
PDF=OUT/'Otoskop_2.0.0_Testaufbau.pdf'
c=canvas.Canvas(str(PDF),pagesize=(W,H))
c.setTitle('Otoskop 2.0.0 - Testaufbau ohne externe Kondensatoren')
c.setAuthor('Projekt Digitales Otoskop')
c.setSubject('Ohne externe Kondensatoren/Sicherung; 10k-Teiler und Softwarefilter; Firmware 2.0.0')
svg=[]

def line(x1,y1,x2,y2,color=INK,width=1.2,dash=False):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width)
    c.setDash(4,3) if dash else c.setDash()
    c.line(x1,H-y1,x2,H-y2)
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="4 3"' if dash else '')+'/>')

def path(points,color=INK,width=1.2):
    for a,b in zip(points,points[1:]):line(*a,*b,color,width)

def rect(x,y,w,h,fill=None,color=GRID):
    c.setStrokeColor(HexColor(color));c.setLineWidth(1);c.setDash()
    if fill:c.setFillColor(HexColor(fill))
    c.rect(x,H-y-h,w,h,stroke=1,fill=bool(fill))
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill or "none"}" stroke="{color}"/>')

def circle(x,y,r=2.6,color=INK,fill=None):
    c.setDash();c.setStrokeColor(HexColor(color));c.setFillColor(HexColor(fill or color));c.circle(x,H-y,r,stroke=1,fill=1)
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{color}" fill="{fill or color}"/>')

def poly(points,color=INK,fill=None):
    p=c.beginPath();p.moveTo(points[0][0],H-points[0][1])
    for x,y in points[1:]:p.lineTo(x,H-y)
    p.close();c.setDash();c.setStrokeColor(HexColor(color))
    if fill:c.setFillColor(HexColor(fill))
    c.drawPath(p,stroke=1,fill=bool(fill))
    svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+f'" stroke="{color}" fill="{fill or "none"}"/>')

def text(x,y,s,size=10,color=INK,bold=False,align='left'):
    font='Arial-Bold' if bold else 'Arial'
    tw=pdfmetrics.stringWidth(s,font,size)
    tx=x-{'left':0,'center':tw/2,'right':tw}[align]
    assert 25<=tx and tx+tw<W-25,(s,tx,tw)
    assert 25<=y<H-25,(s,y)
    c.setFont(font,size);c.setFillColor(HexColor(color));c.drawString(tx,H-y,s)
    svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{dict(left="start",center="middle",right="end")[align]}">{escape(s)}</text>')

def para(x,y,s,width,size=10,leading=14,color=MUTED):
    row=''
    for word in s.split():
        new=(row+' '+word).strip()
        if row and pdfmetrics.stringWidth(new,'Arial',size)>width:
            text(x,y,row,size,color);y+=leading;row=word
        else:row=new
    if row:text(x,y,row,size,color)
    return y

def ground(x,y):
    line(x,y,x,y+8)
    for off,wid in [(8,11),(12,7),(16,3)]:line(x-wid,y+off,x+wid,y+off)

def resistor(x,y,ref,value,vertical=True,color=INK):
    if vertical:
        line(x,y-25,x,y-15,color);rect(x-5,y-15,10,30,'#ffffff',color);line(x,y+15,x,y+25,color)
        text(x+10,y-3,ref,9,color,True);text(x+10,y+11,value,9,color)
    else:
        line(x-30,y,x-20,y,color);rect(x-20,y-5,40,10,'#ffffff',color);line(x+20,y,x+30,y,color)
        text(x,y-22,ref,9,color,True,'center');text(x,y-9,value,9,color,False,'center')

def led(x,y,ref,show_ref=True):
    line(x,y-28,x,y-13);poly([(x-10,y-13),(x+10,y-13),(x,y+9)],INK,'#fff9df')
    line(x-11,y+10,x+11,y+10);line(x,y+10,x,y+28)
    for xx,yy in [(x+15,y-10),(x+20,y+1)]:
        line(xx,yy,xx+9,yy-9,AMBER)
        poly([(xx+9,yy-9),(xx+3,yy-7),(xx+7,yy-3)],AMBER,AMBER)
    text(x-16,y-6,'A',8,MUTED,align='right');text(x-16,y+18,'K',8,MUTED,align='right')
    if show_ref:text(x,y+44,ref,9,bold=True,align='center')

# Header.
rect(28,28,W-56,H-56)
text(46,59,'GLIA / OTOSKOP 2.0.0',12,GREEN,True)
text(W-46,59,'18.11.2026  |  TESTAUFBAU REV 2.0',10,MUTED,align='right')
text(46,94,'Elektrischer Testaufbau',26,bold=True)
text(46,117,'Ohne externe Kondensatoren. Original-XIAO und Sense bleiben werkseitig bestückt. Firmware 2.0.0.',11,MUTED)
line(46,137,W-46,137,GRID)

# Supply. Battery -> S1 -> VBAT_SW; no fuse and no detachable ring connector.
text(62,172,'Versorgung',12,bold=True)
text(62,188,'B1: XTAR 14500-800',9,MUTED)
text(62,201,'geschützt, im Halter',9,MUTED)
path([(90,250),(90,210),(185,210)],RED)
circle(185,210,3,RED,'#ffffff');circle(235,210,3,RED,'#ffffff')
line(185,210,226,191,RED,1.5);line(235,210,405,210,RED)
text(209,166,'S1',10,bold=True,align='center')
text(209,180,'EIN / AUS',8,MUTED,align='center')
text(309,199,'VBAT_SW',10,RED,True,align='center')
line(76,250,104,250,RED,2);line(82,264,98,264,INK,2)
text(112,251,'+',12,RED,True);text(112,270,'-',12,bold=True)
text(112,302,'3,6 V',9,MUTED);text(112,317,'4,2 V voll',9,MUTED)
line(90,264,90,390)
ground(90,390)
text(175,275,'Direkte Akkuversorgung',10,bold=True)
para(175,298,'Keine zusätzlichen Kondensatoren. Originalmodule unverändert verwenden. Akku-, Masse- und LED-Leitungen kurz und direkt führen.',190,10,15)

# Board abstraction; original module connections stay internal.
rect(405,200,330,250,PALE,INK)
text(420,214,'BAT+',10,RED,True)
text(570,246,'U1  XIAO ESP32-S3 Sense',15,bold=True,align='center')
text(570,267,'Lader und Spannungsregler integriert',10,MUTED,align='center')
rect(430,285,280,67,'#ffffff',GRID)
text(570,307,'Original-Sense-Erweiterung',11,bold=True,align='center')
text(570,326,'Kamera + microSD-Steckplatz',10,align='center')
text(570,342,'Modulstecker verwenden; keine Einzelverdrahtung',8.4,MUTED,align='center')
text(420,365,'LAD_ADC / D5 GPIO6',9,BLUE,True)
text(720,365,'USB_ADC / D1 GPIO2',9,BLUE,True,align='right')
line(395,361,405,361,BLUE);line(735,361,745,361,BLUE)
text(420,383,'D3 / GPIO4',11,BLUE,True)
text(420,397,'INPUT_PULLUP',8,BLUE)
text(720,404,'D0 / GPIO1',11,BLUE,True,align='right')
text(650,435,'D4 / GPIO5',10,BLUE,True,align='center')
text(540,435,'BAT- / GND',10,bold=True,align='center')
line(540,450,540,457);ground(540,457)
# USB is a separate physical port, not part of the battery switch.
rect(509,153,122,27,'#ffffff',BLUE);text(570,171,'USB-C am XIAO',10,BLUE,True,align='center')
line(570,180,570,200,BLUE)

# Shutter with internal pull-up: no external resistor required.
rect(46,455,328,190,color=GRID)
text(62,478,'Fotoauslöser',12,bold=True)
path([(405,387),(393,387),(393,505),(200,505),(200,535)],BLUE)
circle(200,535,3,BLUE,'#ffffff');circle(200,575,3,BLUE,'#ffffff')
line(200,535,183,565,BLUE,1.5)
# Dashed mechanical actuator denotes a momentary push contact.
line(173,552,185,552,BLUE,dash=True);line(168,544,168,560,BLUE)
line(200,575,200,603);ground(200,603)
text(233,545,'S2  Taster',11,bold=True)
text(233,563,'Schließer',9,MUTED)
text(233,579,'nach GND',9,MUTED)
text(62,635,'GPIO4: interner Pull-up in Firmware 2.0.0 aktiv.',9,MUTED)

# Status LED, driven from GPIO5, with its own resistor.
rect(405,480,330,165,color=GRID)
text(421,502,'Status-LED',12,bold=True)
path([(650,450),(650,535),(630,535)],BLUE)
resistor(600,535,'R9','1 kOhm',False,BLUE)
path([(570,535),(460,535),(460,545)],BLUE)
led(460,573,'D5',False)
line(460,601,460,619);ground(460,619)
text(510,574,'D5  weiß',11,bold=True)
text(510,593,'Anode A an R9, Kathode K an GND',9,MUTED)
text(510,611,'Bereitschaft / Foto / Ladestatus',9,MUTED)

# Four independently current-limited illumination branches.
rect(770,155,374,490,color=GRID)
text(786,177,'Gehörgangbeleuchtung',12,bold=True)
text(786,195,'VBAT_SW',10,RED,True)
line(790,210,1100,210,RED)
for i,x in enumerate([810,900,990,1080],1):
    circle(x,210,color=RED);line(x,210,x,235,RED)
    resistor(x,260,f'R{i}','220 Ohm')
    line(x,285,x,292)
    led(x,320,f'D{i}')
    line(x,348,x,385);circle(x,385)
line(810,385,1100,385)
path([(1100,385),(1100,420),(990,420),(990,502)])
text(1077,408,'LED_K',9,bold=True,align='right')
# AO3400A, gate isolated, N-channel body/source tie, intrinsic diode.
line(966,502,990,502)
line(957,500,957,561);line(942,503,942,558)
for y in (505,528,551):line(966,y-6,966,y+6,INK,1.8)
path([(966,551),(990,551),(990,620)])
path([(990,551),(990,528),(978,528)])
poly([(968,528),(978,524),(978,532)],INK,INK)
path([(990,502),(1016,502),(1016,516)])
line(1008,516,1024,516)
poly([(1016,519),(1008,534),(1024,534)],INK)
path([(1016,534),(1016,551),(990,551)])
text(1038,485,'Q1  AO3400A',11,bold=True)
text(1038,504,'3 = Drain',9)
text(1038,523,'1 = Gate',9,BLUE)
text(1038,542,'2 = Source',9)
# D0 gate drive and pulldown; no crossing of the LED power path.
path([(735,400),(750,400),(750,535),(770,535)],BLUE)
resistor(800,535,'R5','100 Ohm',False,BLUE)
line(830,535,942,535,BLUE)
circle(880,535,color=BLUE);line(880,535,880,550,BLUE)
resistor(880,575,'R6','100 kOhm')
line(880,600,880,620);line(880,620,990,620);circle(990,620);ground(990,620)
text(786,463,'Vier weiße LEDs, je ein Vorwiderstand.',9,MUTED)
text(786,479,'Licht nur zur Offline-Aufnahme;',9,MUTED)
text(786,495,'im WLAN-Modus per App dimmbar.',9,MUTED)

# Two lower-impedance ADC dividers without external capacitors. CHG0-K is the cathode / nCHG side of
# the existing red on-board LED, not its 5-V anode. Values are external parts.
def sense(x, title, source, first, second, target):
    rect(x,665,540,105,PALE,GRID)
    text(x+16,683,title,11,bold=True)
    text(x+16,713,source,8.5,BLUE)
    line(x+69,710,x+109,710,BLUE)
    resistor(x+139,710,first,'10 kOhm',False,BLUE)
    line(x+169,710,x+510,710,BLUE)
    node=x+204
    circle(node,710,color=BLUE)
    line(node,710,node,722,BLUE);rect(node-5,722,10,20,'#ffffff',INK)
    line(node,742,node,750)
    text(node+14,730,second,8.5,bold=True);text(node+14,743,'10 kOhm',8.5)
    ground(node,750)
    text(x+310,734,'Mehrfachmessung + Entstörung',9,MUTED)
    text(x+310,751,'in Firmware 2.0.0',9,MUTED)
    text(x+510,704,target,9,BLUE,True,align='right')

sense(46,'Ladesignal','CHG0-K','R10','R11','LAD_ADC: D5 / GPIO6')
sense(604,'USB-Erkennung','5V / VBUS','R12','R13','USB_ADC: D1 / GPIO2')
line(46,778,W-46,778,GRID)
text(46,796,'Gleiche Netznamen verbinden (auch VBAT_SW / GND). 5V nie direkt an GPIO2/6. Testentwurf; Hardwareprüfung ausstehend.',9,MUTED)
text(W-46,796,'A3 quer | 1 / 1',9,MUTED,align='right')
text(46,811,'Referenzen: Seeed XIAO (Schaltplan V1.51) | AOS AO3400A | SG Micro SGM40567 (Ladestatus)',8,BLUE)
c.linkURL('https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/new-res/202003753_XIAO%20ESP32S3%20Sense_V1.51_SCH_260611.pdf',(46,H-813,225,H-801),relative=0,thickness=0)
c.linkURL('https://www.aosmd.com/res/data_sheets/AO3400A.pdf',(235,H-813,310,H-801),relative=0,thickness=0)
c.linkURL('https://www.sg-micro.com/rect/assets/e95e555a-a8a2-4761-b86a-6554dff2d8ed/SGM40567.pdf',(320,H-813,550,H-801),relative=0,thickness=0)
c.showPage();c.save()
(HW/'Otoskop_2.0.0_Testaufbau.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>'+''.join(svg)+'</svg>',encoding='utf-8')

nets={
 'BAT_RAW':['B1.+','S1.A'],
 'VBAT_SW':['S1.B','U1.BAT+','R1.1','R2.1','R3.1','R4.1'],
 'GND':['B1.-','U1.BAT-','U1.GND','Q1.2(S)','R6.2','S2.2','D5.K','R11.2','R13.2'],
 'LED_PWM':['U1.D0(GPIO1)','R5.1'],
 'GATE':['R5.2','R6.1','Q1.1(G)'],
 'LED_K':['D1.K','D2.K','D3.K','D4.K','Q1.3(D)'],
 'SHUTTER':['U1.D3(GPIO4)','S2.1'],
 'STATUS_GPIO':['U1.D4(GPIO5)','R9.1'],
 'STATUS_ANODE':['R9.2','D5.A'],
 'CHARGE_RAW':['U1.CHG0.K(nCHG)','R10.1'],
 'LAD_ADC':['R10.2','R11.1','U1.D5(GPIO6)'],
 'USB_5V':['U1.5V(VBUS)','R12.1'],
 'USB_ADC':['R12.2','R13.1','U1.D1(GPIO2)'],
 **{f'LED_A{i}':[f'R{i}.2',f'D{i}.A'] for i in range(1,5)},
}
endpoints=[ep for values in nets.values() for ep in values]
assert len(endpoints)==len(set(endpoints))
assert all('F1' not in ep and 'J2' not in ep and not re.match(r'C\d+\.',ep) for ep in endpoints)
rows=[
 ['01','Halter +','S1 Kontakt A','BAT_RAW'],
 ['02','S1 Kontakt B','XIAO BAT+','VBAT_SW'],
 ['03','VBAT_SW','R1-R4 je Eingang','VBAT_SW'],
 ['04','Halter -','XIAO BAT- / GND','GND'],
 ['05','XIAO D0 / GPIO1','R5 (100 Ohm)','LED_PWM'],
 ['06','R5 Ausgang','Q1 Gate / Pin 1 und R6.1','GATE'],
 ['07','R6.2 (100 kOhm)','GND','GND'],
 ['08','R1-R4 je Ausgang','D1-D4 je Anode A','LED_A1..4'],
 ['09','D1-D4 je Kathode K','Q1 Drain / Pin 3','LED_K'],
 ['10','Q1 Source / Pin 2','GND','GND'],
 ['12','XIAO D3 / GPIO4','S2 Kontakt 1','SHUTTER'],
 ['13','S2 Kontakt 2','GND','GND'],
 ['14','XIAO D4 / GPIO5','R9 (1 kOhm)','STATUS_GPIO'],
 ['15','R9 Ausgang','D5 Anode A','STATUS_ANODE'],
 ['16','D5 Kathode K','GND','GND'],
 ['17','U1 rote Lade-LED, Kathode / nCHG','R10 (10 kOhm)','CHARGE_RAW'],
 ['18','R10 Ausgang','D5 / GPIO6 und R11.1','LAD_ADC'],
 ['19','R11.2','GND','GND'],
 ['20','XIAO 5V / VBUS','R12 (10 kOhm)','USB_5V'],
 ['21','R12 Ausgang','D1 / GPIO2 und R13.1','USB_ADC'],
 ['22','R13.2','GND','GND'],
]
for i,row in enumerate(rows,1): row[0] = f'{i:02d}'
with (HW/'Otoskop_2.0.0_Netzliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['Netz','Anschluss','Art'])
    for net,values in nets.items():
        for ep in values:w.writerow([net,ep,'extern'])
with (HW/'Otoskop_2.0.0_Drahtliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['Nummer','Von','Nach','Netz']);w.writerows(rows)
(HW/'Otoskop_2.0.0_Netze.json').write_text(json.dumps(nets,ensure_ascii=False,indent=2)+'\n')
print(f'Erstellt: {PDF}, 1 SVG, Drahtliste und Netzliste. LIGHT=1, SHUTTER=4, STATUS=5, CHARGE=6, USB=2 geprüft.')
