"""Consolida la matriz y crea el informe PDF a partir de Markdown y fichas.

Requiere reportlab y pypdf. Ejecutar desde cualquier directorio con Python 3.
No consulta servicios externos ni modifica el estado de Active Stack/OpenSpec.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "discovery"
DATE = "2026-10-15"
STATUS = "Once puntos y revisión personal de seis fuentes confirmados"
WEIGHTS = {
    "turnos": 25, "clinica": 20, "integraciones": 15,
    "administracion": 15, "paciente": 10, "seguridad": 10, "precio": 5,
}

# Orden por pertinencia para Argentina y el TP; nunca se ordena por score.
# Resúmenes editoriales: los detalles y límites viven en las fichas enlazadas.
PRODUCTS = [
    ("denteo", "Denteo", "Datasoluciones / Argentina", "Consultorio y clínica dental", "SaaS/navegador", "https://denteo.com.ar/clinica.html", "D: vistas, recursos y bloqueos", "D: odontograma/evoluciones", "D: WhatsApp manual; C: ARCA", "C: ARS/mes; cupos fechados; divergencias previas"),
    ("dentalink", "Dentalink", "Healthatom / Chile; oferta Argentina", "Individual, clínica y sucursales", "Nube/navegador", "https://web-ar.softwaredentalink.com/", "D: agenda y reserva con recursos", "C: módulos dentales", "C: WhatsApp/obras sociales AR", "C: cotización; importe NE"),
    ("dentidesk", "DENTIDESK", "DENTIDESK CHILE SpA / Chile", "Clínica dental; académico separado", "SaaS", "https://www.dentidesk.com/", "C: intervalos y reserva web", "C: anamnesis y especialidades", "D: WhatsApp manual; AR NE", "D: prueba 15 días; tarifa NE"),
    ("odontosoft", "OdontoSoft Millennium", "GB Systems / Argentina y USA", "Consultorio y clínica dental", "Windows; web opcional", "https://gbsystems.com/os/", "D histórico: asignación/concurrencia", "D histórico: odontograma/pagos", "WhatsApp y ARCA NE", "C: USD compra; vigencia pendiente"),
    ("doctoralia-argentina", "Doctoralia Argentina", "Doctoralia / origen y entidad AR NE; oferta Argentina", "Especialista y centro de salud", "Agenda online", "https://pro.doctoralia.com/ar/agenda-doctoralia-para-especialistas", "D: duración, consulta y servicios", "C: registro; dental específico NE", "C: WhatsApp; pagos AR NE", "C: ARS/mes facturado anual"),
    ("agendapro", "AgendaPro", "AgendaPro Inc. / país de origen NE; oferta Argentina", "Citas multirrubro; oferta dental", "Nube", "https://agendapro.com/ar/dental/software-odontologico", "D: vistas, recursos y bloqueos", "C: ficha, imágenes y evolución", "C: WhatsApp; fiscal próximo", "C: ARS/mes; WhatsApp extra"),
    ("odontosys", "Odontosys", "Razón social NE / Uruguay", "Consultorio dental", "Windows, web y móvil", "https://odontosys.com/", "D: crear, editar y duración", "C: ficha/odontograma/perio", "D: confirmar/cancelar WhatsApp", "C: cotización; importe NE"),
    ("simples-dental", "Simples Dental", "Entidad jurídica NE / Brasil", "Consultorio, clínica y redes", "Web y móvil", "https://www.simplesdental.com/", "C: sillones, bloqueos y enlace", "C: odontograma y tratamiento", "C: WhatsApp; pagos brasileños", "C: BRL/mes con cobro anual"),
    ("dental-office", "Dental Office", "Entidad jurídica NE / Brasil", "Consultorio y clínica dental", "Online/app según plan", "https://www.dentaloffice.com.br/", "C: dentista, enlace y espera", "C: odontograma; perio opcional", "C: WhatsApp; Pix/NF Brasil", "C: BRL mensual/anual; extras"),
    ("clinic-cloud", "Clinic Cloud", "Doctoralia España/Internet SL / España", "Clínica multiespecialidad/dental", "Navegador", "https://clinic-cloud.com/tarifas", "D: cita, box opcional y duración", "C: odontograma/perio por módulo", "D: WhatsApp asistido; AR NE", "C: EUR/mes + IVA; extras"),
    ("gesden", "GESDEN ONE/G5", "INFOMED SOFTWARE SL / España", "Clínica dental", "ONE servicio; G5 licencia", "https://www.infomedsoftware.com/software/gesden/gesden-one/", "D: reserva G5; límites de variante", "C: módulos ONE", "D: WhatsApp G5; fiscal AR NE", "D: propuesta; importe NE"),
    ("open-dental", "Open Dental", "Open Dental Software / USA", "Consultorio y clínica dental", "Autohospedado; cloud US", "https://www.opendental.com/", "D: recursos, bloques y reglas", "D: chart, perio e imágenes", "WhatsApp/local AR NE", "D: USD/sede/mes; servicios extra"),
    ("dentrix-ascend", "Dentrix Ascend", "Henry Schein One / USA", "Consultorio, grupo y DSO", "Cloud", "https://www.dentrixascend.com/", "D: alta, duración y aviso conflicto", "D: informe clínico", "WhatsApp/local AR NE", "C: cotización; importe NE"),
    ("carestack", "CareStack", "Good Methods Global Inc. / USA", "Consultorio, grupo y DSO", "Cloud", "https://carestack.com/company", "D: bloques y double booking", "D: notas, perio e historia", "WhatsApp/local AR NE", "C: monto mensual; moneda NE"),
    ("dentisoft", "Dentisoft", "Dentisoft Technologies / USA", "Consultorio dental", "Cloud; Desktop distinto", "https://dentisoft.com/corporate.html", "C: agenda; controles NE", "C: registros/charting Pro", "WhatsApp/local AR NE", "C: Starter gratis; moneda NE"),
]


def replace_section(document: str, name: str, content: str) -> str:
    pattern = rf"(<!-- {name}:start -->).*?(<!-- {name}:end -->)"
    result, count = re.subn(pattern, lambda m: f"{m[1]}\n{content}\n{m[2]}", document, flags=re.S)
    if count != 1:
        raise ValueError(f"Se esperaba un único bloque {name}; hay {count}")
    return result


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    all_rows = [headers, ["---"] * len(headers), *rows]
    return "\n".join("| " + " | ".join(row) + " |" for row in all_rows)


def consolidate() -> dict:
    if len(PRODUCTS) != 15 or sum(WEIGHTS.values()) != 100:
        raise ValueError("La matriz exige quince productos y pesos que sumen 100")
    matrix = []
    identity, coverage, score_rows = [], [], []
    references: dict[str, list[tuple[str, str]]] = {}
    distinct = set()
    for slug, name, company, segment, modality, website, agenda, clinical, local, price in PRODUCTS:
        path = OUT / "fuentes" / f"{slug}.md"
        note = path.read_text(encoding="utf-8")
        # Normalizar los finales de línea evita cambios de hash por el checkout
        # CRLF de Windows cuando el contenido documental es el mismo.
        raw = note.encode("utf-8")
        lines = re.findall(r"^Puntajes: (.+)$", note, flags=re.M)
        if len(lines) != 1:
            raise ValueError(f"{slug}: falta una única línea Puntajes")
        scores = {key: int(value) for key, value in re.findall(r"([a-z]+)=(\d+)", lines[0])}
        if set(scores) != set(WEIGHTS) or any(value not in range(6) for value in scores.values()):
            raise ValueError(f"{slug}: dimensiones o scores inválidos")
        total = sum(Decimal(WEIGHTS[key]) * Decimal(scores[key]) / Decimal(5) for key in WEIGHTS)
        urls = []
        for label, url in re.findall(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", note):
            if url not in {item[1] for item in urls}:
                urls.append((label, url))
            distinct.add(url)
        if not urls:
            raise ValueError(f"{slug}: ficha sin URL pública")
        references[name] = urls
        matrix.append({"producto": name, "ficha": f"fuentes/{slug}.md", "sha256": hashlib.sha256(raw).hexdigest(), "puntajes": scores, "total": float(total)})
        link = f"[{name}](fuentes/{slug}.md)"
        identity.append([link, company, segment, modality, f"[Oficial]({website}); {DATE}"])
        coverage.append([link, agenda, clinical, local, price])
        score_rows.append([name, *[str(scores[key]) for key in WEIGHTS], f"{total:g}/100"])
    law_path = OUT / "fuentes" / "marco-argentino.md"
    laws = re.findall(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", law_path.read_text(encoding="utf-8"))
    references["Marco argentino"] = laws
    ref_lines = []
    for name, urls in references.items():
        ref_lines.extend([f"## {name}", ""])
        ref_lines.extend(f"- {label}: [{url}]({url}). Consulta: {DATE}." for label, url in urls)
        ref_lines.append("")
    document_path = OUT / "informe-discovery.md"
    document = document_path.read_text(encoding="utf-8")
    document = replace_section(document, "identity", markdown_table(["Producto / ficha", "Empresa y país", "Segmento", "Modalidad", "URL y consulta"], identity))
    document = replace_section(document, "coverage", markdown_table(["Producto", "Agenda", "Clínica", "Argentina / WhatsApp", "Oferta"], coverage))
    document = replace_section(document, "matrix", markdown_table(["Producto", "T 25", "C 20", "I 15", "A 15", "P 10", "S 10", "Pr 5", "Total"], score_rows))
    document = replace_section(document, "references", "\n".join(ref_lines))
    document_path.write_text(document, encoding="utf-8", newline="\n")
    result = {"estado": STATUS, "fecha": DATE, "metrica": "Cobertura documental pública; no calidad real", "formula": "sum(peso * puntaje / 5)", "pesos": WEIGHTS, "productos": matrix, "urls_unicas_en_fichas_productos": len(distinct), "leyes_referenciadas": len(laws)}
    (OUT / "matriz-evidencia.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def normalize(text: str) -> str:
    return text.replace("—", "-").replace("–", "-").replace("‑", "-").replace("\u200b", "").replace("\u00a0", " ")


def inline(text: str) -> str:
    text = html.escape(normalize(text))
    def link(match):
        label, url = match.groups()
        if url.startswith(("https://", "http://")):
            return f'<link href="{url}" color="#087F8C">{label}</link>'
        return f'<font color="#087F8C">{label}</font>'
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    return text


def register_fonts() -> None:
    fonts = Path("C:/Windows/Fonts")
    for name, filename in [("Arial", "arial.ttf"), ("ArialBold", "arialbd.ttf"), ("ArialItalic", "ariali.ttf"), ("ArialBoldItalic", "arialbi.ttf")]:
        font = fonts / filename
        if not font.is_file():
            raise FileNotFoundError(f"Fuente requerida no disponible: {font}")
        pdfmetrics.registerFont(TTFont(name, str(font)))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="ArialBold", italic="ArialItalic", boldItalic="ArialBoldItalic")


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="BodyAR", fontName="Arial", fontSize=9.4, leading=13, textColor=colors.HexColor("#243447"), spaceAfter=7, splitLongWords=True))
    base.add(ParagraphStyle(name="LeadAR", parent=base["BodyAR"], keepWithNext=True))
    base.add(ParagraphStyle(name="HeadingAR", fontName="ArialBold", fontSize=21, leading=27, textColor=colors.HexColor("#112E45"), spaceAfter=16, keepWithNext=True))
    base.add(ParagraphStyle(name="SubAR", fontName="ArialBold", fontSize=12.2, leading=17, textColor=colors.HexColor("#087F8C"), spaceBefore=12, spaceAfter=8, keepWithNext=True))
    base.add(ParagraphStyle(name="CellAR", fontName="Arial", fontSize=8.0, leading=11.2, textColor=colors.HexColor("#243447"), spaceAfter=0, splitLongWords=True))
    base.add(ParagraphStyle(name="HeadCellAR", parent=base["CellAR"], fontName="ArialBold", textColor=colors.white))
    base.add(ParagraphStyle(name="RefAR", parent=base["BodyAR"], fontSize=7.7, leading=11.2, wordWrap="CJK", spaceAfter=6))
    return base


def table_flow(rows: list[list[str]], st, width: float):
    count = len(rows[0])
    if count == 9:
        widths = [width * .285] + [width * .071] * 7 + [width * .218]
        widths = [value * width / sum(widths) for value in widths]
    elif count == 5:
        widths = [width * ratio for ratio in [.175, .23, .185, .19, .22]]
    elif count == 3:
        widths = [width * ratio for ratio in [.24, .31, .45]]
    else:
        widths = [width * .28, width * .72] if count == 2 else [width / count] * count
    cells = [[Paragraph(inline(value), st["HeadCellAR"] if row_index == 0 else st["CellAR"]) for value in row] for row_index, row in enumerate(rows)]
    table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123C51")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F6F8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), .7, colors.HexColor("#087F8C")),
        ("LINEBELOW", (0, 1), (-1, -1), .3, colors.HexColor("#D7E2E6")),
    ]))
    # Las comparaciones y la matriz caben en una página completa: conservarlas
    # juntas permite comparar los quince productos sin perder filas al pasarla.
    return KeepTogether([table]) if count in (5, 9) else table


def render_markdown(text: str, st, width: float, skip_top_title=False, references=False):
    flow = []
    lines = text.splitlines()
    index, paragraph = 0, []
    in_refs = references
    def flush():
        if paragraph:
            body = " ".join(paragraph)
            style = st["RefAR"] if in_refs else st["LeadAR"] if body.startswith("**Nombre propuesto:**") else st["BodyAR"]
            flow.append(Paragraph(inline(body), style))
            paragraph.clear()
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("<!--") or not line:
            flush()
            index += 1
            continue
        if line.startswith("|"):
            flush()
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                row = [item.strip() for item in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in row):
                    rows.append(row)
                index += 1
            if any(len(row) != len(rows[0]) for row in rows):
                raise ValueError("Tabla Markdown con columnas inconsistentes")
            flow.extend([table_flow(rows, st, width), Spacer(1, 10)])
            continue
        if line.startswith("# "):
            flush()
            if skip_top_title:
                skip_top_title = False
            else:
                flow.extend([PageBreak(), Paragraph(inline(line[2:]), st["HeadingAR"])])
                in_refs = line.startswith("# Referencias")
            index += 1
            continue
        if line.startswith("## ") or line.startswith("### "):
            flush()
            flow.append(Paragraph(inline(line.lstrip("# ")), st["SubAR"]))
            index += 1
            continue
        if line.startswith("- "):
            flush()
            flow.append(Paragraph("&#8226; " + inline(line[2:]), st["RefAR"] if in_refs else st["BodyAR"]))
        else:
            paragraph.append(line)
        index += 1
    flush()
    return flow


def footer(canvas, doc):
    page = doc.page
    canvas.saveState()
    width, height = A4
    if page > 1:
        canvas.setStrokeColor(colors.HexColor("#D5E3E7"))
        canvas.line(42, height - 35, width - 42, height - 35)
        canvas.setFont("Arial", 7.6)
        canvas.setFillColor(colors.HexColor("#476477"))
        canvas.drawString(42, height - 27, "TP-ODONTOLOGIA | Discovery | Informe de trabajo")
    canvas.setFont("Arial", 7.5)
    canvas.setFillColor(colors.HexColor("#476477"))
    canvas.drawString(42, 25, "15/10/2026 | Datos ficticios | Revisión personal de fuentes confirmada")
    canvas.drawRightString(width - 42, 25, str(page))
    canvas.restoreState()


def create_pdf(matrix: dict):
    register_fonts()
    st = styles()
    width = A4[0] - 84
    pdf_path = OUT / "informe-discovery.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=52, bottomMargin=47, title="Discovery - Gestión de turnos odontológicos - Informe de trabajo", author="Responsable de revisión: estudiante; integrante pendiente", subject="Relevamiento documental asistido por IA para Metodología I", pageCompression=1)
    cover_title = ParagraphStyle("CoverTitle", fontName="ArialBold", fontSize=32, leading=40, textColor=colors.HexColor("#112E45"), spaceAfter=24)
    cover_small = ParagraphStyle("CoverSmall", parent=st["BodyAR"], fontSize=12, leading=19, spaceAfter=18)
    flow = [Spacer(1, 54), Paragraph("METODOLOGÍA I", st["SubAR"]), Spacer(1, 18), Paragraph("Discovery<br/>Gestión de turnos<br/>odontológicos", cover_title), HRFlowable(width="100%", thickness=3, color=colors.HexColor("#087F8C")), Spacer(1, 24), Paragraph("INFORME DE TRABAJO", cover_small), Paragraph("Consultorio pequeño de Argentina<br/>Primer change: profesional y box sin solapamientos", cover_small), Spacer(1, 24), Paragraph("15 de octubre de 2026<br/>Integrante/autor de la entrega: pendiente de identificación", st["BodyAR"]), Spacer(1, 18), Paragraph(f"15 productos | 7 criterios | {matrix['urls_unicas_en_fichas_productos']} URLs referenciadas en fichas<br/>Relevamiento documental con asistencia de IA. Sin demos ejecutadas.", st["BodyAR"]), Paragraph("Confirmé los once puntos de Discovery y continuaré con la fundación.<br/>Delegué una revisión adicional de seis fuentes a IA.<br/>Confirmé que vi las seis fuentes y me parecen bien (15/10/2026).<br/>Este informe todavía no constituye la entrega académica final.", st["BodyAR"]), PageBreak()]
    main = (OUT / "informe-discovery.md").read_text(encoding="utf-8")
    # La portada Markdown queda en la fuente; en PDF tiene diseño independiente.
    main = "## Resumen ejecutivo" + main.split("## Resumen ejecutivo", 1)[1]
    flow.extend(render_markdown(main, st, width))
    for index, product in enumerate(PRODUCTS, start=1):
        slug, name = product[:2]
        flow.extend([PageBreak(), Paragraph(f"Anexo {index:02d}. {html.escape(name)}", st["HeadingAR"]), Paragraph(f"Ficha detallada de evidencia pública. Fuente local: fuentes/{slug}.md", st["BodyAR"])])
        note = (OUT / "fuentes" / f"{slug}.md").read_text(encoding="utf-8")
        flow.extend(render_markdown(note, st, width, skip_top_title=True))
    flow.extend([PageBreak(), Paragraph("Anexo 16. Marco argentino", st["HeadingAR"])])
    flow.extend(render_markdown((OUT / "fuentes" / "marco-argentino.md").read_text(encoding="utf-8"), st, width, skip_top_title=True))
    flow.extend([PageBreak(), Paragraph("Anexo 17. Once puntos confirmados", st["HeadingAR"])])
    flow.extend(render_markdown((OUT / "resumen-para-revision.md").read_text(encoding="utf-8"), st, width, skip_top_title=True))
    flow.extend([PageBreak(), Paragraph("Anexo 18. Revisión documental delegada", st["HeadingAR"])])
    review_st = styles()
    review_st["CellAR"].fontSize = 7.6
    review_st["CellAR"].leading = 10
    flow.extend(render_markdown((OUT / "revision-documental-2026-10-15.md").read_text(encoding="utf-8"), review_st, width, skip_top_title=True))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    required = ["INFORME DE TRABAJO", "Resumen ejecutivo", "A. Comparación", "B. Matriz", "C. Hallazgos", "D. Referencias", "Verificación de fuentes", "Anexo 17", "Anexo 18", *[product[1] for product in PRODUCTS]]
    absent = [item for item in required if item not in text]
    if absent:
        raise ValueError(f"Texto esperado ausente en PDF: {absent}")
    if any(len(page.extract_text() or "") < 80 for page in reader.pages):
        raise ValueError("PDF con página vacía o extracción insuficiente")
    print(json.dumps({"pdf": str(pdf_path), "paginas": len(reader.pages), "productos": len(PRODUCTS), "scores": 105, "urls_productos": matrix["urls_unicas_en_fichas_productos"], "checks_texto": "PASS", "totales": {p["producto"]: p["total"] for p in matrix["productos"]}}, ensure_ascii=False))


if __name__ == "__main__":
    create_pdf(consolidate())
