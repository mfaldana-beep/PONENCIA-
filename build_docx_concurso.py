#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el .docx conforme al reglamento del XVI Concurso Internacional Junior
de Derecho Procesal Constitucional (Cartagena 2026):
- Papel Carta, fuente Arial 12, interlineado 1.5, margenes 3 cm en todos los lados.
- Titulos en numeracion arabiga.
- Portada con titulo, integrantes, tutor/director y universidad.
- Citas a pie de pagina (reglas editoriales de la UNAM), via sintaxis ^[...].
Uso: python3 build_docx_concurso.py ENTRADA.md SALIDA.docx
"""
import re, zipfile, os, sys
from xml.sax.saxutils import escape

SRC, OUT = sys.argv[1], sys.argv[2]
FONT = 'Arial'
CM = 566.9  # twips por cm
MARGIN = int(round(3 * CM))  # 3 cm = 1701 twips

footnotes = []  # lista de textos de nota (id = indice+1)

def frun(text, bold=False, ital=False, sz=24):
    rpr = '<w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (FONT, FONT, sz, sz)
    if bold: rpr += '<w:b/>'
    if ital: rpr += '<w:i/>'
    return '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))

def footnote_ref(note_text):
    footnotes.append(note_text)
    fid = len(footnotes)  # 1-indexed; separadores usan -1 y 0
    rpr = '<w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="24"/><w:vertAlign w:val="superscript"/>' % (FONT, FONT)
    return '<w:r><w:rPr>%s</w:rPr><w:footnoteReference w:id="%d"/></w:r>' % (rpr, fid), fid

def inline(text):
    """Procesa ^[nota], **negrita**, *cursiva* -> runs XML."""
    out = []
    # dividir por notas al pie primero
    parts = re.split(r'(\^\[[^\]]*\])', text)
    for part in parts:
        if part.startswith('^[') and part.endswith(']'):
            note = part[2:-1]
            r, _ = footnote_ref(note)
            out.append(r)
            continue
        # negrita/cursiva
        for seg in re.split(r'(\*\*.+?\*\*|\*.+?\*)', part):
            if not seg:
                continue
            if seg.startswith('**') and seg.endswith('**'):
                out.append(frun(seg[2:-2], bold=True))
            elif seg.startswith('*') and seg.endswith('*'):
                out.append(frun(seg[1:-1], ital=True))
            else:
                out.append(frun(seg))
    return ''.join(out)

def para(text, align='both', indent=709, before=0, after=120):
    ppr = '<w:spacing w:line="360" w:lineRule="auto" w:before="%d" w:after="%d"/><w:jc w:val="%s"/>' % (before, after, align)
    if indent:
        ppr += '<w:ind w:firstLine="%d"/>' % indent
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, inline(text))

def list_item(text):
    ppr = '<w:spacing w:line="360" w:lineRule="auto" w:after="60"/><w:jc w:val="both"/><w:ind w:left="709" w:hanging="284"/>'
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, inline(text))

def heading(text, level):
    sz = {1: 28, 2: 26, 3: 25, 4: 24}.get(level, 24)
    before, after = (300, 140) if level <= 2 else (200, 100)
    r = '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:b/><w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (FONT, FONT, sz, sz, escape(text))
    ppr = '<w:spacing w:before="%d" w:after="%d" w:line="360" w:lineRule="auto"/><w:jc w:val="left"/><w:keepNext/>' % (before, after)
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, r)

def title_para(text, sz=32, after=160, center=True, bold=True):
    r = '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="%d"/><w:szCs w:val="%d"/>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (FONT, FONT, sz, sz, '<w:b/>' if bold else '', escape(text))
    jc = 'center' if center else 'both'
    ppr = '<w:spacing w:before="0" w:after="%d" w:line="360" w:lineRule="auto"/><w:jc w:val="%s"/>' % (after, jc)
    return '<w:p><w:pPr>%s</w:pPr>%s</w:p>' % (ppr, r)

def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

def empty(n=1):
    return ''.join('<w:p><w:pPr><w:spacing w:after="0"/></w:pPr></w:p>' for _ in range(n))

def cell(text, header=False):
    rpr = '<w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="22"/><w:szCs w:val="22"/>' % (FONT, FONT)
    if header: rpr += '<w:b/>'
    r = '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))
    shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/>' if header else ''
    tcpr = '<w:tcPr><w:tcW w:w="4508" w:type="dxa"/>%s</w:tcPr>' % shade
    return '<w:tc>%s<w:p><w:pPr><w:spacing w:line="276" w:lineRule="auto" w:after="40"/></w:pPr>%s</w:p></w:tc>' % (tcpr, r)

def table(rows):
    b = ''.join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="000000"/>' % s for s in ['top','left','bottom','right','insideH','insideV'])
    tblpr = '<w:tblPr><w:tblW w:w="9016" w:type="dxa"/><w:tblBorders>%s</w:tblBorders></w:tblPr>' % b
    grid = '<w:tblGrid><w:gridCol w:w="4508"/><w:gridCol w:w="4508"/></w:tblGrid>'
    body = ''.join('<w:tr>%s</w:tr>' % ''.join(cell(c, header=(ri == 0)) for c in row) for ri, row in enumerate(rows))
    return '<w:tbl>%s%s%s</w:tbl><w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>' % (tblpr, grid, body)

with open(SRC, encoding='utf-8') as f:
    lines = f.read().split('\n')

body = [page_break()]  # portada ocupa la primera pagina (se antepone luego)

# ---- cuerpo ----
i, n = 0, len(lines)
in_refs = False
cover_done = False
cover_block = []
# La portada se define con un bloque delimitado por <!--PORTADA--> ... <!--/PORTADA-->
text = '\n'.join(lines)
mcov = re.search(r'<!--PORTADA-->(.*?)<!--/PORTADA-->', text, re.DOTALL)
cover_lines = mcov.group(1).strip().split('\n') if mcov else []
if mcov:
    text = text.replace(mcov.group(0), '')
lines = text.split('\n')

# construir portada
cover = []
cover.append(empty(2))
for cl in cover_lines:
    s = cl.strip()
    if not s:
        cover.append(empty(1)); continue
    if s.startswith('# '):
        cover.append(title_para(s[2:].strip(), 30, 200))
    elif s.startswith('## '):
        cover.append(title_para(s[3:].strip(), 24, 160, bold=False))
    elif s.startswith('@@'):
        cover.append(title_para(s[2:].strip(), 22, 60, bold=True))
    else:
        cover.append(title_para(s, 22, 60, bold=False))

i, n = 0, len(lines)
while i < n:
    line = lines[i].rstrip()
    s = line.strip()
    if s == '---' or s == '':
        i += 1; continue
    if s.startswith('#### '):
        body.append(heading(s[5:].strip(), 4)); i += 1; continue
    if s.startswith('### '):
        body.append(heading(s[4:].strip(), 3)); i += 1; continue
    if s.startswith('## '):
        txt = s[3:].strip(); low = txt.lower()
        if low.startswith('bibliograf') or low.startswith('referencias') or low.startswith('fuentes'):
            in_refs = True
        body.append(heading(txt, 2)); i += 1; continue
    if s.startswith('# '):
        body.append(heading(s[2:].strip(), 1)); i += 1; continue
    if s.startswith('|'):
        tbl = []
        while i < n and lines[i].strip().startswith('|'):
            tbl.append(lines[i].strip()); i += 1
        rows = []
        for tl in tbl:
            core = tl.replace('|','').replace(' ','').replace(':','')
            if core and set(core) <= {'-'}: continue
            rows.append([c.strip() for c in tl.strip('|').split('|')])
        body.append(table(rows)); continue
    if in_refs:
        if s.startswith('### '):
            body.append(heading(s[4:].strip(), 3)); i += 1; continue
        if s.startswith('*Nota'):
            body.append(para(s, indent=0)); i += 1; continue
        body.append('<w:p><w:pPr><w:spacing w:line="360" w:lineRule="auto" w:after="120"/><w:jc w:val="both"/><w:ind w:left="709" w:hanging="709"/></w:pPr>%s</w:p>' % inline(s))
        i += 1; continue
    if s.startswith('- [ ]') or s.startswith('- [x]'):
        body.append(list_item('\u2610  ' + s[5:].strip())); i += 1; continue
    if s.startswith('- '):
        body.append(list_item('\u2022  ' + s[2:].strip())); i += 1; continue
    m = re.match(r'^(\d+)\.\s+(.*)$', s)
    if m:
        body.append(list_item('%s.  %s' % (m.group(1), m.group(2)))); i += 1; continue
    if (s.startswith('**Resumen') or s.startswith('**Abstract') or s.startswith('**Palabras')
            or s.startswith('**Keywords') or s.startswith('**Sumario') or s.startswith('*Nota')):
        body.append(para(s, indent=0)); i += 1; continue
    body.append(para(s)); i += 1

document_body = ''.join(cover) + page_break() + ''.join(body)

# ---- footnotes.xml ----
fn_items = ['<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>',
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>']
for idx, note in enumerate(footnotes, start=1):
    run_note = '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="20"/><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteRef/></w:r>' % (FONT, FONT)
    run_txt = '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="20"/></w:rPr><w:t xml:space="preserve"> %s</w:t></w:r>' % (FONT, FONT, escape(note))
    fn_items.append('<w:footnote w:id="%d"><w:p><w:pPr><w:spacing w:line="240" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>%s%s</w:p></w:footnote>' % (idx, run_note, run_txt))
footnotes_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                 + ''.join(fn_items) + '</w:footnotes>')

footer_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
              '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
              '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
              '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="20"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
              '<w:r><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
              '</w:p></w:ftr>') % (FONT, FONT, FONT, FONT, FONT, FONT)

sectpr = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/>'
          '<w:pgSz w:w="12240" w:h="15840"/>'
          '<w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" w:header="720" w:footer="720" w:gutter="0"/>'
          '</w:sectPr>') % (MARGIN, MARGIN, MARGIN, MARGIN)

document_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<w:body>%s%s</w:body></w:document>') % (document_body, sectpr)

content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                 '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
                 '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                 '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                 '</Types>')

rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '</Relationships>')

doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
            '<Relationship Id="rIdFootnotes" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>'
            '<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
            '</Relationships>')

styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="es-CO"/></w:rPr></w:rPrDefault></w:docDefaults>'
          '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="24"/></w:rPr></w:style>'
          '</w:styles>') % (FONT, FONT, FONT, FONT)

settings = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:zoom w:percent="100"/><w:defaultTabStop w:val="708"/><w:footnotePr><w:numFmt w:val="decimal"/></w:footnotePr></w:settings>')

core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>Estandar etico del debido proceso algoritmico en la jurisdiccion constitucional</dc:title>'
        '<dc:creator>Equipo concursante</dc:creator><dc:language>es-CO</dc:language></cp:coreProperties>')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', content_types)
    z.writestr('_rels/.rels', rels)
    z.writestr('word/document.xml', document_xml)
    z.writestr('word/_rels/document.xml.rels', doc_rels)
    z.writestr('word/styles.xml', styles)
    z.writestr('word/settings.xml', settings)
    z.writestr('word/footnotes.xml', footnotes_xml)
    z.writestr('word/footer1.xml', footer_xml)
    z.writestr('docProps/core.xml', core)

print('OK ->', OUT, os.path.getsize(OUT), 'bytes;', len(footnotes), 'notas al pie')
