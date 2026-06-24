#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convierte PONENCIA_ESTANDAR_ETICO.md en un .docx con formato academico (APA-like).

Soporta encabezados (##, ###), parrafos con **negrita** y *cursiva*, listas con vinetas,
listas numeradas, items de verificacion (- [ ]), tablas Markdown y seccion de referencias
con sangria francesa. Times New Roman 12, interlineado 1.5, portada y pie con numero de pagina.
"""
import re, zipfile, os
from xml.sax.saxutils import escape

SRC = os.path.join(os.path.dirname(__file__), "PONENCIA_ESTANDAR_ETICO.md")
OUT = os.path.join(os.path.dirname(__file__), "PONENCIA_ESTANDAR_ETICO.docx")


def runs(text):
    """Convierte **bold** y *italic* en runs XML. TNR 12 (24 half-pts)."""
    out = []
    pattern = re.compile(r'(\*\*.+?\*\*|\*.+?\*)')
    parts = pattern.split(text)
    for p in parts:
        if not p:
            continue
        bold = ital = False
        if p.startswith('**') and p.endswith('**'):
            bold = True; p = p[2:-2]
        elif p.startswith('*') and p.endswith('*'):
            ital = True; p = p[1:-1]
        rpr = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/>'
        if bold: rpr += '<w:b/>'
        if ital: rpr += '<w:i/>'
        out.append('<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(p)))
    return ''.join(out)


def para(text, align='both', spacing=360, indent=708, before=0, after=120, style_runs=None):
    ppr = '<w:spacing w:line="%d" w:lineRule="auto" w:before="%d" w:after="%d"/>' % (spacing, before, after)
    ppr += '<w:jc w:val="%s"/>' % align
    if indent:
        ppr += '<w:ind w:firstLine="%d"/>' % indent
    body = style_runs if style_runs is not None else runs(text)
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, body)


def list_item(text, numbered=False):
    """Item de lista con sangria izquierda, sin sangria de primera linea."""
    ppr = '<w:spacing w:line="360" w:lineRule="auto" w:after="60"/><w:jc w:val="both"/><w:ind w:left="708" w:hanging="284"/>'
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, runs(text))


def heading(text, level):
    if level == 1:
        sz = 30; before = 360; after = 160
    else:
        sz = 26; before = 240; after = 120
    rpr = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    r = '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))
    ppr = '<w:spacing w:before="%d" w:after="%d" w:line="360" w:lineRule="auto"/><w:jc w:val="left"/><w:keepNext/>' % (before, after)
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, r)


def title_para(text, sz=36, after=160, center=True, bold=True):
    rpr = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    if bold: rpr += '<w:b/>'
    r = '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))
    jc = 'center' if center else 'both'
    ppr = '<w:spacing w:before="0" w:after="%d" w:line="360" w:lineRule="auto"/><w:jc w:val="%s"/>' % (after, jc)
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, r)


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def empty(n=1):
    return ''.join('<w:p><w:pPr><w:spacing w:after="0"/></w:pPr></w:p>' for _ in range(n))


def cell(text, header=False):
    rpr = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/><w:szCs w:val="22"/>'
    if header:
        rpr += '<w:b/>'
    r = '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))
    shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/>' if header else ''
    tcpr = '<w:tcPr><w:tcW w:w="4675" w:type="dxa"/>%s</w:tcPr>' % shade
    ppr = '<w:pPr><w:spacing w:line="276" w:lineRule="auto" w:after="40"/><w:jc w:val="left"/></w:pPr>'
    return '<w:tc>%s<w:p>%s%s</w:p></w:tc>' % (tcpr, ppr, r)


def table(rows):
    """rows: lista de listas de celdas (strings). Primera fila = encabezado."""
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               '</w:tblBorders>')
    tblpr = '<w:tblPr><w:tblW w:w="9350" w:type="dxa"/>%s</w:tblPr>' % borders
    grid = '<w:tblGrid><w:gridCol w:w="4675"/><w:gridCol w:w="4675"/></w:tblGrid>'
    body = ''
    for ridx, row in enumerate(rows):
        cells = ''.join(cell(c, header=(ridx == 0)) for c in row)
        body += '<w:tr>%s</w:tr>' % cells
    spacer = '<w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>'
    return '<w:tbl>%s%s%s</w:tbl>%s' % (tblpr, grid, body, spacer)


# --- Leer markdown ---
with open(SRC, encoding='utf-8') as f:
    lines = f.read().split('\n')

body = []
# ===== PORTADA =====
body.append(empty(3))
body.append(title_para("ESTÁNDAR ÉTICO DEL DEBIDO PROCESO ALGORÍTMICO EN LA JURISDICCIÓN CONSTITUCIONAL", 32, 120))
body.append(title_para("Manual de buenas prácticas para la aplicación de inteligencia artificial con protección de los derechos fundamentales en la jurisdicción constitucional", 24, 200, bold=False))
body.append(empty(2))
body.append(title_para("Ethical Standards for Algorithmic Due Process in Constitutional Jurisdiction", 22, 120, bold=False))
body.append(empty(1))
body.append(title_para("Dirigido a operadores judiciales", 22, 120, bold=False))
body.append(empty(6))
body.append(title_para("Bogotá D.C., Colombia", 24, 80, bold=False))
body.append(title_para("2026", 24, 80, bold=False))
body.append(page_break())

# ===== CUERPO =====
i = 0
n = len(lines)
in_refs = False
first_h1_done = False

while i < n:
    line = lines[i].rstrip()
    s = line.strip()

    if s == '---' or s == '':
        i += 1; continue

    if s.startswith('# '):
        # titulo principal: ya esta en portada
        i += 1; continue

    if s.startswith('## '):
        txt = s[3:].strip()
        if txt.lower().startswith('referencias'):
            in_refs = True
            body.append(page_break())
        body.append(heading(txt, 1))
        i += 1; continue

    if s.startswith('### '):
        body.append(heading(s[4:].strip(), 2))
        i += 1; continue

    # Tabla Markdown
    if s.startswith('|'):
        tbl_lines = []
        while i < n and lines[i].strip().startswith('|'):
            tbl_lines.append(lines[i].strip())
            i += 1
        rows = []
        for tl in tbl_lines:
            # saltar la fila separadora |---|---|
            if re.match(r'^\|[\s:|-]+\|?$', tl) and set(tl.replace('|', '').replace(' ', '').replace(':', '')) <= {'-'}:
                continue
            parts = [c.strip() for c in tl.strip('|').split('|')]
            rows.append(parts)
        body.append(table(rows))
        continue

    # Referencias: sangria francesa
    if in_refs:
        if s.startswith('*Nota'):
            body.append(para(s, align='both', indent=0))
            i += 1; continue
        body.append('<w:p><w:pPr><w:spacing w:line="360" w:lineRule="auto" w:after="120"/><w:jc w:val="both"/><w:ind w:left="708" w:hanging="708"/></w:pPr>%s</w:p>' % runs(s))
        i += 1; continue

    # Checklist
    if s.startswith('- [ ]') or s.startswith('- [x]'):
        txt = '☐ ' + s[5:].strip()
        body.append(list_item(txt))
        i += 1; continue

    # Lista con vinetas
    if s.startswith('- '):
        txt = '•  ' + s[2:].strip()
        body.append(list_item(txt))
        i += 1; continue

    # Lista numerada
    m = re.match(r'^(\d+)\.\s+(.*)$', s)
    if m:
        txt = '%s.  %s' % (m.group(1), m.group(2))
        body.append(list_item(txt, numbered=True))
        i += 1; continue

    # Abstract / palabras clave / producto / poblacion / nota
    if (s.startswith('**Resumen.**') or s.startswith('**Abstract.**') or
            s.startswith('**Palabras clave:**') or s.startswith('**Keywords:**') or
            s.startswith('**Producto:**') or s.startswith('**Población dirigida:**') or
            s.startswith('*Nota')):
        body.append(para(s, align='both', indent=0))
        i += 1; continue

    body.append(para(s))
    i += 1

document_body = ''.join(body)

footer_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p><w:pPr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>
</w:p></w:ftr>'''

sectpr = '''<w:sectPr>
<w:footerReference w:type="default" r:id="rIdFooter"/>
<w:pgSz w:w="12240" w:h="15840"/>
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
</w:sectPr>'''

document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>%s%s</w:body>
</w:document>''' % (document_body, sectpr)

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>'''

rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>'''

doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''

styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="es-CO"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
</w:styles>'''

settings = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:zoom w:percent="100"/><w:defaultTabStop w:val="708"/></w:settings>'''

core = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Estándar ético del debido proceso algorítmico en la jurisdicción constitucional</dc:title>
<dc:creator>Ponencia</dc:creator><dc:language>es-CO</dc:language></cp:coreProperties>'''

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', content_types)
    z.writestr('_rels/.rels', rels)
    z.writestr('word/document.xml', document_xml)
    z.writestr('word/_rels/document.xml.rels', doc_rels)
    z.writestr('word/styles.xml', styles)
    z.writestr('word/settings.xml', settings)
    z.writestr('word/footer1.xml', footer_xml)
    z.writestr('docProps/core.xml', core)

print("OK ->", OUT, os.path.getsize(OUT), "bytes")
