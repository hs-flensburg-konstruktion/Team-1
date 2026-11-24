#!/usr/bin/env python3
"""Generate the separate minimal first-test circuit; full circuit stays intact."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/Otoskop_2.0.0_Erster_Testaufbau.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
fonts = Path('/System/Library/Fonts/Supplemental')
for name, file in [('Arial', 'Arial.ttf'), ('Arial-Bold', 'Arial Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
W, H = landscape(A4)
INK, MUTED, BLUE, RED, GREEN, BORDER = '#173047', '#526779', '#146b9a', '#b6323c', '#187259', '#ccd8e1'
c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle('Otoskop 2.0.0 - Erster Testaufbau mit einer Beleuchtungs-LED')
c.setAuthor('Projekt Digitales Otoskop')

def line(x1, y1, x2, y2, color=INK, width=1.2):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(width)
    c.line(x1, H-y1, x2, H-y2)

def path(points, color=INK):
    for a, b in zip(points, points[1:]): line(*a, *b, color)

def text(x, y, value, size=9, color=INK, bold=False, align='left'):
    font = 'Arial-Bold' if bold else 'Arial'
    width = pdfmetrics.stringWidth(value, font, size)
    x -= {'left': 0, 'center': width/2, 'right': width}[align]
    assert 26 <= x and x+width <= W-26, (value, x, width)
    c.setFont(font, size); c.setFillColor(HexColor(color)); c.drawString(x, H-y, value)

def box(x, y, w, h, fill='#ffffff', stroke=BORDER):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke)); c.setLineWidth(.8)
    c.rect(x, H-y-h, w, h, stroke=1, fill=1)

def dot(x, y, color=INK, hollow=False):
    c.setStrokeColor(HexColor(color)); c.setFillColor(HexColor('#ffffff' if hollow else color))
    c.circle(x, H-y, 2.2, stroke=1, fill=1)

def ground(x, y):
    line(x, y, x, y+5)
    for off, half in [(5, 8), (9, 5), (13, 2)]: line(x-half, y+off, x+half, y+off)

def resistor(x, y, ref, value, vertical=False):
    if vertical:
        line(x, y-21, x, y-13); box(x-4, y-13, 8, 26, stroke=INK); line(x, y+13, x, y+21)
        text(x+9, y-2, ref, 8, bold=True); text(x+9, y+10, value, 8)
    else:
        line(x-25, y, x-17, y); box(x-17, y-4, 34, 8, stroke=INK); line(x+17, y, x+25, y)
        text(x, y-20, ref, 8, bold=True, align='center'); text(x, y-8, value, 8, align='center')

def led(x, y):
    line(x, y-22, x, y-10)
    p = c.beginPath(); p.moveTo(x-8,H-y+10); p.lineTo(x+8,H-y+10); p.lineTo(x,H-y-7); p.close()
    c.setStrokeColor(HexColor(INK)); c.setFillColor(HexColor('#fff5cd')); c.drawPath(p, stroke=1, fill=1)
    line(x-9,y+8,x+9,y+8); line(x,y+8,x,y+22)
    for dx,dy in [(13,-8),(18,1)]:
        line(x+dx,y+dy,x+dx+7,y+dy-7)
        line(x+dx+7,y+dy-7,x+dx+3,y+dy-6)
        line(x+dx+7,y+dy-7,x+dx+6,y+dy-3)
    text(x-13,y-4,'A',7,MUTED,align='right'); text(x-13,y+17,'K',7,MUTED,align='right')

def header(page, subtitle):
    text(30,32,'OTOSKOP 2.0.0 / ERSTER TESTAUFBAU',10,GREEN,True)
    text(W-30,32,f'24.11.2026  |  {page} / 2',8,MUTED,align='right')
    text(30,62,subtitle,22,bold=True)
    line(30,78,W-30,78,BORDER)

def footer(value):
    line(30,552,W-30,552,BORDER)
    text(30,570,value,8,MUTED)

header(1,'Schaltplan mit einer Beleuchtungs-LED')
text(30,98,'Firmware 2.0.0. Keine Ladezustandserkennung, keine zusätzlichen Kondensatoren.',10,MUTED)
text(30,114,'Gleich benannte Netze sind elektrisch verbunden. Alle GND-Symbole miteinander verbinden.',9,MUTED)

# Battery holder and main switch.
box(30,132,242,184)
text(42,151,'1  Akku und Hauptschalter',11,bold=True)
line(60,212,60,187,RED); line(60,187,130,187,RED)
line(50,212,70,212,RED,2); line(54,224,66,224,INK,2)
text(78,215,'+',10,RED,True); text(78,230,'-',10,bold=True)
line(60,224,60,245); ground(60,245)
dot(130,187,RED,True); dot(170,187,RED,True); line(130,187,163,173,RED)
line(170,187,242,187,RED); text(242,179,'VBAT_SW',8,RED,True,align='right')
text(151,163,'S1 EIN/AUS',8,bold=True,align='center')
text(95,241,'B1: Halter + geschützter',9)
text(95,255,'14500-Li-Ion-Akku',9)
text(42,282,'Nennspannung 3,6 / 3,7 V; maximal 4,2 V.',8,MUTED)
text(42,299,'Keine gewöhnliche 1,5-V-AA-Batterie verwenden.',8,MUTED)

# Board with named nets; not a physical pad placement drawing.
box(292,132,255,184,'#f4f7fa',INK)
text(419,154,'XIAO ESP32-S3 Sense',13,bold=True,align='center')
text(419,170,'Funktionsblock, keine Pad-Anordnung',8,MUTED,align='center')
line(292,187,310,187,RED); text(317,190,'BAT+ = VBAT_SW',9,RED,True)
text(308,214,'Kamera + Sense-Erweiterung + microSD',10,bold=True)
text(308,230,'Original-Modulstecker benutzen.',9,MUTED)
text(308,246,'FAT32-Karte einsetzen; 4-32 GB vorgesehen.',9,MUTED)
text(308,269,'D0 / GPIO1: LED_PWM',9,BLUE,True)
text(308,284,'D3 / GPIO4: AUSLOESER',9,BLUE,True)
text(308,299,'D4 / GPIO5: STATUS',9,BLUE,True)
line(547,187,555,187); ground(555,187)
text(545,179,'BAT- / GND',8,bold=True,align='right')

# One illumination branch, identical low-side MOSFET driver to full circuit.
box(567,132,245,321)
text(579,151,'2  Eine Beleuchtungs-LED',11,bold=True)
text(721,174,'VBAT_SW',8,RED,True,align='right')
line(695,180,695,188,RED)
resistor(695,209,'R1','220 Ohm',True)
line(695,230,695,240); led(695,262); line(695,284,695,310)
text(736,260,'D1',9,bold=True); text(736,275,'weiß',8)
# MOSFET symbol, gate 1, drain 3, source 2; intrinsic body diode.
line(671,310,695,310); line(662,308,662,358); line(650,310,650,355)
for y in (313,333,353): line(671,y-5,671,y+5,width=1.8)
path([(671,353),(695,353),(695,410)])
path([(695,353),(695,333),(681,333)])
line(673,333,681,329); line(673,333,681,337); line(681,329,681,337)
path([(695,310),(713,310),(713,322)])
line(706,322,720,322)
line(713,325,706,338); line(706,338,720,338); line(720,338,713,325)
path([(713,338),(713,353),(695,353)])
text(738,310,'Q1',9,bold=True); text(738,324,'AO3400A',8,bold=True)
text(738,339,'3 Drain',8); text(738,353,'1 Gate',8); text(738,367,'2 Source',8)
text(579,351,'LED_PWM',8,BLUE,True)
line(580,333,585,333,BLUE); resistor(610,333,'R5','100 Ohm'); line(635,333,650,333,BLUE)
dot(641,333,BLUE); line(641,333,641,363)
resistor(641,384,'R6','100 kOhm',True)
line(641,405,641,410); line(641,410,695,410); dot(695,410); ground(695,410)
text(579,441,'D0 / GPIO1 steuert das Licht über Q1.',8,MUTED)

# Pushbutton; open contact is not a toggle switch.
box(30,334,242,119)
text(42,354,'3  Auslösetaster',11,bold=True)
text(42,375,'AUSLOESER',8,BLUE,True)
line(115,372,137,372,BLUE); dot(137,372,BLUE,True); dot(177,372,BLUE,True)
line(137,372,170,358,BLUE); line(155,346,155,355,BLUE); line(148,346,162,346,BLUE)
line(177,372,220,372); ground(220,372)
text(42,404,'S2: Schließer, nur während Drücken geschlossen.',8)
text(42,420,'An D3 / GPIO4 und GND; kein Widerstand nötig.',8)
text(42,438,'Interner Pull-up ist in Firmware 2.0.0 aktiv.',8,MUTED)

# External status LED.
box(292,334,255,119)
text(304,354,'4  Weiße Status-LED',11,bold=True)
text(304,383,'STATUS',8,BLUE,True)
line(345,380,355,380,BLUE); resistor(380,380,'R9','1 kOhm')
path([(405,380),(438,380),(438,381)]); led(438,403); line(438,425,438,430); ground(438,430)
text(479,404,'D5',9,bold=True); text(479,418,'weiß',8)
text(304,411,'D4 / GPIO5 an R9;',8,MUTED)
text(304,427,'Kathode K an GND.',8,MUTED)

# Deliberate temporary ground links for unpopulated charge sensing.
box(30,469,782,65,'#f4f7fa')
text(42,488,'5  Ladeerkennung entfällt beim ersten Test',10,bold=True)
text(42,505,'D1 / GPIO2  ---  Brücke A  ---  GND',9,BLUE,True)
text(42,521,'D5 / GPIO6  ---  Brücke B  ---  GND',9,BLUE,True)
text(350,505,'Beide Messeingänge auf GND legen, damit sie nicht offen bleiben.',9)
text(350,521,'Nicht an 5V oder die rote Onboard-LED anschließen. Später Brücken entfernen.',8.5,MUTED)
footer('D1 und D5 als Bauteilnamen sind LEDs. XIAO D1 und XIAO D5 bezeichnen dagegen Anschlusspads.')
c.showPage()

header(2,'Löthilfe und erster Funktionstest')
text(30,100,'Anschlussnamen am XIAO prüfen. GPIO-Nummern und D-Bezeichnungen sind nicht identisch.',10,MUTED)

# Explicit soldering table.
rows = [
 ('1','Halter Plus','S1 Kontakt A'),
 ('2','S1 Kontakt B','BAT+ am XIAO und R1 Eingang (VBAT_SW)'),
 ('3','Halter Minus','BAT- / GND am XIAO und gemeinsame Masse'),
 ('4','R1 Ausgang (220 Ohm)','Anode A der Beleuchtungs-LED D1'),
 ('5','Kathode K der Beleuchtungs-LED D1','Q1 Drain, Pin 3'),
 ('6','Q1 Source, Pin 2','GND'),
 ('7','XIAO D0 / GPIO1','R5 Eingang (100 Ohm)'),
 ('8','R5 Ausgang','Q1 Gate, Pin 1 und R6 Eingang'),
 ('9','R6 Ausgang (100 kOhm)','GND'),
 ('10','XIAO D3 / GPIO4','S2 Kontakt 1; S2 Kontakt 2 an GND'),
 ('11','XIAO D4 / GPIO5','R9 Eingang (1 kOhm)'),
 ('12','R9 Ausgang','Anode A der Status-LED D5; Kathode K an GND'),
 ('13','XIAO D1 / GPIO2','GND über abnehmbare Brücke A'),
 ('14','XIAO D5 / GPIO6','GND über abnehmbare Brücke B'),
]
table_y = 116
box(30,table_y,782,22,'#173047',INK)
for x,s in [(40,'Nr.'),(75,'Von'),(352,'Nach')]: text(x,table_y+15,s,9,'#ffffff',True)
for i,(n,a,b) in enumerate(rows):
    y=table_y+22+i*19
    box(30,y,782,19,'#f4f7fa' if i%2==0 else '#ffffff')
    for x,s in [(40,n),(75,a),(352,b)]: text(x,y+13,s,8.5)

text(30,430,'Bauteile',11,bold=True)
text(30,447,'XIAO ESP32-S3 Sense mit Kamera; FAT32-microSD; geschützter 14500-Li-Ion-Akku mit Halter;',9)
text(30,462,'S1 EIN/AUS-Schalter; S2 Schließertaster; 2 weiße LEDs; Q1 AO3400A; je 1x 220 Ohm, 100 Ohm, 100 kOhm und 1 kOhm.',9)

text(30,486,'Vor dem Einschalten',11,bold=True)
text(30,502,'Ohne Akku und USB löten. Polung und Kurzschlüsse prüfen. Akku-, Masse- und LED-Leitungen kurz halten.',9)
text(30,517,'Q1 ist SOT-23: Pinbelegung anhand des Datenblatts prüfen; das Schaltbild zeigt keine mechanische Anordnung.',9)
text(30,532,'USB bleibt trotz S1 AUS aktiv. Werksbauteile bleiben bestückt; keine zusätzlichen Kondensatoren nötig.',9)
footer('Test auf dem Tisch: normal starten, Statuslicht abwarten, auslösen. Nach 2x Blinken JPEG unter /photos auf der Karte prüfen.')
c.showPage()
c.save()
print(OUT)
