#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera PRESENTACION_MANUAL.pdf: diapositivas horizontales con diseno para
presentar el resultado (capitulo final / Manual de buenas practicas).
PDF en Python puro con fuentes base-14 (Helvetica) y WinAnsiEncoding.
"""
import zlib, struct

W, H = 792.0, 612.0  # US Letter horizontal (puntos)
objects = []

def add_obj(body):
    objects.append(body)
    return len(objects)  # numero de objeto (1-indexed)

def esc(s):
    return s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')

# medir ancho aproximado (Helvetica ~0.52 em promedio)
def text_width(s, size, bold=False):
    return len(s) * size * (0.55 if bold else 0.52)

def wrap(text, size, max_w, bold=False):
    words = text.split(' ')
    lines = []
    cur = ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if text_width(trial, size, bold) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# colores (RGB 0-1)
NAVY = (0.09, 0.16, 0.33)
BLUE = (0.14, 0.35, 0.60)
GOLD = (0.83, 0.66, 0.22)
LIGHT = (0.94, 0.95, 0.97)
GREEN = (0.16, 0.44, 0.30)
RED = (0.60, 0.16, 0.16)
WHITE = (1, 1, 1)
DARK = (0.13, 0.13, 0.16)
GREYBOX = (0.90, 0.92, 0.95)

class Slide:
    def __init__(self):
        self.ops = []
    def rect(self, x, y, w, h, color, fill=True):
        r, g, b = color
        if fill:
            self.ops.append('%.3f %.3f %.3f rg' % (r, g, b))
            self.ops.append('%.2f %.2f %.2f %.2f re f' % (x, y, w, h))
        else:
            self.ops.append('%.3f %.3f %.3f RG' % (r, g, b))
            self.ops.append('%.2f %.2f %.2f %.2f re S' % (x, y, w, h))
    def text(self, x, y, s, size, color=DARK, bold=False):
        r, g, b = color
        font = 'F2' if bold else 'F1'
        data = esc(s)
        self.ops.append('BT /%s %.1f Tf %.3f %.3f %.3f rg %.2f %.2f Td (%s) Tj ET' % (font, size, r, g, b, x, y, data))
    def paragraph(self, x, y, text, size, max_w, leading, color=DARK, bold=False):
        for ln in wrap(text, size, max_w, bold):
            self.text(x, y, ln, size, color, bold)
            y -= leading
        return y
    def stream(self):
        return '\n'.join(self.ops)

slides = []

def header(sl, kicker, title, band=NAVY):
    sl.rect(0, 0, W, H, LIGHT)
    sl.rect(0, H-96, W, 96, band)
    sl.rect(0, H-100, W, 4, GOLD)
    sl.text(56, H-46, kicker, 12, GOLD, bold=True)
    sl.text(56, H-78, title, 24, WHITE, bold=True)
    sl.rect(0, 30, W, 22, band)
    sl.text(56, 36, 'Estandar etico del debido proceso algoritmico - Manual de buenas practicas', 9, WHITE)
    sl.text(W-120, 36, 'Jurisdiccion constitucional', 9, GOLD)

# --- Slide 1: PORTADA ---
s = Slide()
s.rect(0, 0, W, H, NAVY)
s.rect(0, H-8, W, 8, GOLD)
s.rect(0, 0, W, 8, GOLD)
s.rect(70, 300, 200, 6, GOLD)
s.text(70, 430, 'RESULTADO DE LA PONENCIA', 14, GOLD, bold=True)
s.paragraph(70, 390, 'Estandar etico del debido proceso algoritmico en la jurisdiccion constitucional', 30, W-140, 38, WHITE, bold=True)
s.paragraph(70, 250, 'Manual de buenas practicas para la aplicacion de inteligencia artificial con proteccion de los derechos fundamentales', 16, W-160, 22, (0.85, 0.88, 0.93))
s.text(70, 150, 'Poblacion dirigida: operadores judiciales', 13, GOLD, bold=True)
s.text(70, 70, 'Bogota D.C., Colombia  |  2026', 11, (0.8, 0.83, 0.9))
slides.append(s)

# --- Slide 2: PRINCIPIOS ---
s = Slide()
header(s, 'COLUMNA VERTEBRAL', 'Los 8 principios del estandar', NAVY)
princ = [
    ('1. Transparencia y explicabilidad', 'Revelar y documentar el uso de IA; poder explicar su incidencia.'),
    ('2. Control humano significativo', 'La IA apoya; el juez decide. Nada exclusivamente automatizado.'),
    ('3. Responsabilidad y rendicion de cuentas', 'Siempre hay un responsable humano identificable.'),
    ('4. Igualdad y no discriminacion', 'Prevenir y mitigar sesgos; ante indicios, suspender el uso.'),
    ('5. Proteccion de datos y minimizacion', 'Finalidad, necesidad, seguridad; anonimizar cuando sea posible.'),
    ('6. Trazabilidad y auditabilidad', 'Registrar herramienta, finalidad, operador e incidencia.'),
    ('7. Proporcionalidad y prevencion de riesgos', 'Usar la IA solo si es idonea, necesaria y razonable.'),
    ('8. Primacia de los derechos fundamentales', 'Ante tension con la eficiencia, prevalecen los derechos.'),
]
colw = (W - 112 - 24) / 2
x0 = 56
y0 = H - 130
for idx, (t, d) in enumerate(princ):
    col = idx % 2
    row = idx // 2
    bx = x0 + col * (colw + 24)
    by = y0 - row * 106
    s.rect(bx, by-86, colw, 92, WHITE)
    s.rect(bx, by-86, 6, 92, BLUE)
    s.text(bx+18, by-16, t, 12.5, NAVY, bold=True)
    s.paragraph(bx+18, by-40, d, 10.5, colw-34, 14, DARK)
slides.append(s)

# --- Slide 3: PROTOCOLO POR FASES ---
s = Slide()
header(s, 'COMO APLICARLO', 'Protocolo por fases', BLUE)
fases = [
    ('ANTES', BLUE, ['Herramienta idonea y validada', 'Verificar seguridad y datos', 'Descartar apps no autorizadas', 'Definir el proposito']),
    ('DURANTE', GREEN, ['Controlar el razonamiento', 'Resultado = insumo, no decision', 'Verificar veracidad y fuentes', 'No cargar datos sensibles']),
    ('DESPUES', GOLD, ['Revelar el uso en la actuacion', 'Motivacion propia y verificada', 'Registrar trazabilidad', 'Guardar para auditoria']),
]
cw = (W - 112 - 48) / 3
for i, (title, col, items) in enumerate(fases):
    bx = 56 + i * (cw + 24)
    s.rect(bx, 120, cw, 360, WHITE)
    s.rect(bx, 440, cw, 40, col)
    s.text(bx+18, 452, title, 16, WHITE, bold=True)
    yy = 410
    for it in items:
        s.rect(bx+18, yy+3, 7, 7, col)
        yy = s.paragraph(bx+34, yy, it, 11.5, cw-52, 15, DARK) - 12
slides.append(s)

# --- Slide 4: MATRIZ ---
s = Slide()
header(s, 'LIMITES CLAROS', 'Matriz: lo permitido y lo prohibido', NAVY)
perm = ['Clasificar y priorizar expedientes', 'Buscar jurisprudencia (verificada)', 'Apoyar borradores (asumidos)', 'Sintetizar expedientes', 'Traducir o resumir documentos', 'Detectar patrones de gestion']
proh = ['Decidir la seleccion o el fondo', 'Citar fuentes sin verificar', 'Copiar texto sin comprender', 'Datos sensibles en apps inseguras', 'Sustituir la motivacion con IA', 'IA predictiva para prejuzgar']
cw = (W - 112 - 24) / 2
# permitido
s.rect(56, 120, cw, 360, WHITE)
s.rect(56, 440, cw, 40, GREEN)
s.text(74, 452, 'PERMITIDO (apoyo y gestion)', 14, WHITE, bold=True)
yy = 410
for it in perm:
    s.text(74, yy, '+  ' + it, 12, GREEN, bold=True)
    yy -= 44
# prohibido
bx = 56 + cw + 24
s.rect(bx, 120, cw, 360, WHITE)
s.rect(bx, 440, cw, 40, RED)
s.text(bx+18, 452, 'PROHIBIDO (sustitucion y riesgo)', 14, WHITE, bold=True)
yy = 410
for it in proh:
    s.text(bx+18, yy, 'x  ' + it, 12, RED, bold=True)
    yy -= 44
slides.append(s)

# --- Slide 5: DECALOGO ---
s = Slide()
header(s, 'EN DIEZ REGLAS', 'Decalogo del uso etico', BLUE)
deca = [
    'La IA apoya; el juez decide.',
    'Verifica siempre veracidad y fuentes.',
    'Revela el uso cuando incida.',
    'Protege los datos sensibles.',
    'Motiva con razones propias.',
    'Vigila los sesgos; protege a los vulnerables.',
    'Usa solo herramientas validadas.',
    'Deja rastro de lo que usaste.',
    'Asume la responsabilidad humana.',
    'Capacitate: uso critico, no inercia.',
]
colw = (W - 112 - 24) / 2
x0 = 56
y0 = H - 130
for idx, t in enumerate(deca):
    col = idx % 2
    row = idx // 2
    bx = x0 + col * (colw + 24)
    by = y0 - row * 68
    s.rect(bx, by-52, colw, 58, WHITE)
    s.rect(bx, by-52, 40, 58, GOLD)
    s.text(bx+12, by-34, str(idx+1), 22, WHITE, bold=True)
    s.paragraph(bx+52, by-22, t, 12, colw-66, 15, DARK, bold=True)
slides.append(s)

# --- Slide 6: CHECKLIST ---
s = Slide()
header(s, 'ANTES DE FIRMAR', 'Lista de verificacion etica', GREEN)
chk = [
    'La herramienta esta autorizada y validada?',
    'El uso es idoneo, necesario y proporcionado?',
    'Evite datos sensibles en herramientas inseguras?',
    'Verifique veracidad y vigencia de las fuentes?',
    'La motivacion es propia y comprendida?',
    'Evalue sesgos y su impacto en sujetos protegidos?',
    'Revele el uso cuando correspondia?',
    'Registre la trazabilidad para auditoria?',
    'Hay un responsable humano identificado?',
]
yy = H - 140
for it in chk:
    s.rect(66, yy-3, 16, 16, WHITE)
    s.rect(66, yy-3, 16, 16, NAVY, fill=False)
    s.text(96, yy, it, 13.5, DARK)
    yy -= 40
slides.append(s)

# --- Slide 7: GOBERNANZA / CIERRE ---
s = Slide()
header(s, 'SOSTENIBILIDAD', 'Gobernanza, auditoria y responsabilidad', NAVY)
gov = [
    ('Supervision institucional', 'Instancia que autoriza herramientas y supervisa su uso.'),
    ('Auditorias algoritmicas', 'Evaluacion periodica de logica, errores, sesgos y datos.'),
    ('Responsabilidad del operador', 'Reglas claras articuladas con el regimen disciplinario.'),
    ('Capacitacion continua', 'Alfabetizacion algoritmica (Marco de competencias UNESCO).'),
]
yy = H - 140
for t, d in gov:
    s.rect(56, yy-40, W-112, 52, WHITE)
    s.rect(56, yy-40, 6, 52, GOLD)
    s.text(74, yy-8, t, 14, NAVY, bold=True)
    s.paragraph(74, yy-26, d, 11.5, W-200, 14, DARK)
    yy -= 66
s.rect(56, 70, W-112, 46, BLUE)
s.text(74, 92, 'La tecnologia al servicio de los derechos, no a la inversa.', 14, WHITE, bold=True)
slides.append(s)

# ---- ensamblar PDF ----
# objetos: fuentes, paginas, contenidos, pages, catalog
font1 = add_obj('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
font2 = add_obj('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')

page_obj_nums = []
content_obj_nums = []
pages_obj_num_placeholder = None

# reservar numero para Pages
pages_num = len(objects) + 1 + 0  # se calculara luego; usaremos enfoque en dos fases
# Enfoque: primero creamos contenidos y paginas apuntando a un numero de Pages fijo.
# Calculamos pages_num = actual + 2*len(slides) + 1
n_slides = len(slides)
pages_num = len(objects) + 2 * n_slides + 1

for sl in slides:
    stream = sl.stream().encode('latin-1', 'replace')
    comp = zlib.compress(stream)
    cnum = add_obj(('<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(comp)).encode('latin-1') + comp + b'\nendstream')
    content_obj_nums.append(cnum)
    pnum = add_obj('<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.0f %.0f] /Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>' % (pages_num, W, H, font1, font2, cnum))
    page_obj_nums.append(pnum)

kids = ' '.join('%d 0 R' % n for n in page_obj_nums)
pages_actual = add_obj('<< /Type /Pages /Kids [%s] /Count %d >>' % (kids, n_slides))
assert pages_actual == pages_num, (pages_actual, pages_num)
catalog = add_obj('<< /Type /Catalog /Pages %d 0 R >>' % pages_num)

# escribir
out = bytearray()
out += b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
offsets = [0] * (len(objects) + 1)
for i, body in enumerate(objects, start=1):
    offsets[i] = len(out)
    if isinstance(body, bytes):
        out += ('%d 0 obj\n' % i).encode('latin-1') + body + b'\nendobj\n'
    else:
        out += ('%d 0 obj\n%s\nendobj\n' % (i, body)).encode('latin-1')
xref_pos = len(out)
out += ('xref\n0 %d\n' % (len(objects) + 1)).encode('latin-1')
out += b'0000000000 65535 f \n'
for i in range(1, len(objects) + 1):
    out += ('%010d 00000 n \n' % offsets[i]).encode('latin-1')
out += ('trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objects) + 1, catalog, xref_pos)).encode('latin-1')

open('PRESENTACION_MANUAL.pdf', 'wb').write(out)
print('OK -> PRESENTACION_MANUAL.pdf', len(out), 'bytes,', n_slides, 'diapositivas')
