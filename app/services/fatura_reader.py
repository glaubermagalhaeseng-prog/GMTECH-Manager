"""
Leitura de fatura de energia (PDF ou imagem).

Estratégia:
1) PDF texto: pdfplumber + PyMuPDF
2) Tabelas do PDF (pdfplumber)
3) PDF escaneado / foto: OCR (pytesseract + Tesseract), se instalado

Otimizado também para layouts Energisa, CEMIG, ENEL, CPFL, Equatorial, Light.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

# Caminhos comuns do Tesseract no Windows (quando não está no PATH)
_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def _configurar_tesseract() -> bool:
    """Aponta o pytesseract para o executável instalado."""
    try:
        import pytesseract
    except ImportError:
        return False

    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        pass

    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    candidatos = list(_TESSERACT_CANDIDATES)
    if user:
        candidatos.append(
            rf"C:\Users\{user}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
        )

    for caminho in candidatos:
        if caminho and os.path.isfile(caminho):
            pytesseract.pytesseract.tesseract_cmd = caminho
            try:
                pytesseract.get_tesseract_version()
                return True
            except Exception:
                continue
    return False


# Configura na importação do módulo
_configurar_tesseract()


def _extrair_texto_pdf(caminho: str) -> str:
    partes: List[str] = []

    # 1) pdfplumber — texto + tabelas
    try:
        import pdfplumber

        with pdfplumber.open(caminho) as pdf:
            for page in pdf.pages[:5]:
                t = page.extract_text() or ""
                if t.strip():
                    partes.append(t)
                try:
                    for table in page.extract_tables() or []:
                        for row in table:
                            if not row:
                                continue
                            linha = " ".join(
                                str(c).strip() for c in row if c and str(c).strip()
                            )
                            if linha:
                                partes.append(linha)
                except Exception:
                    pass
    except Exception:
        pass

    texto = "\n".join(partes)

    # 2) PyMuPDF (fitz) — costuma pegar texto que o pdfplumber perde
    if len(texto.strip()) < 40:
        try:
            import fitz

            doc = fitz.open(caminho)
            blocos = []
            for i, page in enumerate(doc):
                if i >= 5:
                    break
                blocos.append(page.get_text("text") or "")
                # blocos com posição (melhor em alguns PDFs da Energisa)
                try:
                    td = page.get_text("dict")
                    for b in td.get("blocks", []):
                        for line in b.get("lines", []):
                            s = "".join(
                                span.get("text", "") for span in line.get("spans", [])
                            )
                            if s.strip():
                                blocos.append(s)
                except Exception:
                    pass
            doc.close()
            texto2 = "\n".join(blocos)
            if len(texto2.strip()) > len(texto.strip()):
                texto = texto2
        except Exception:
            pass

    return texto or ""


def _ocr_imagem_pil(img) -> str:
    try:
        import pytesseract

        _configurar_tesseract()

        configs = [
            r"--oem 3 --psm 6",
            r"--oem 3 --psm 4",
            r"--oem 3 --psm 3",
        ]
        textos = []
        for cfg in configs:
            for lang in ("por", "por+eng", "eng"):
                try:
                    t = pytesseract.image_to_string(img, lang=lang, config=cfg)
                    if t and len(t.strip()) > 20:
                        textos.append(t)
                except Exception:
                    try:
                        t = pytesseract.image_to_string(img, config=cfg)
                        if t and len(t.strip()) > 20:
                            textos.append(t)
                    except Exception:
                        pass
        # junta e remove duplicatas grosseiras
        return "\n".join(dict.fromkeys(textos))
    except Exception:
        return ""


def _extrair_texto_imagem(caminho: str) -> str:
    try:
        from PIL import Image, ImageOps, ImageFilter, ImageEnhance

        img = Image.open(caminho)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        # pré-processamento leve
        gray = ImageOps.grayscale(img)
        gray = ImageOps.autocontrast(gray)
        gray = gray.filter(ImageFilter.SHARPEN)
        gray = ImageEnhance.Contrast(gray).enhance(1.4)
        return _ocr_imagem_pil(gray) or _ocr_imagem_pil(img)
    except Exception:
        return ""


def _extrair_texto_pdf_ocr(caminho: str) -> str:
    try:
        import fitz
        from PIL import Image
        import io

        doc = fitz.open(caminho)
        textos = []
        for i, page in enumerate(doc):
            if i >= 3:
                break
            # DPI alto ajuda OCR de fatura Energisa
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            t = _ocr_imagem_pil(img)
            if t:
                textos.append(t)
        doc.close()
        return "\n".join(textos)
    except Exception:
        return ""


def extrair_texto(caminho: str) -> str:
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".pdf":
        texto = _extrair_texto_pdf(caminho)
        if len(texto.strip()) < 60:
            ocr = _extrair_texto_pdf_ocr(caminho)
            if len(ocr.strip()) > len(texto.strip()):
                texto = ocr
        return texto
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"):
        return _extrair_texto_imagem(caminho)
    return ""


def _parse_numero_br(s: str) -> Optional[float]:
    if not s:
        return None
    s = str(s).strip()
    s = s.replace("R$", "").replace("r$", "").replace(" ", "")
    s = re.sub(r"[^\d\.,\-]", "", s)
    if not s or s in (".", ",", "-", "-."):
        return None

    # 1.234.567,89
    if re.match(r"^-?\d{1,3}(\.\d{3})+,\d+$", s):
        s = s.replace(".", "").replace(",", ".")
    # 1,234,567.89
    elif re.match(r"^-?\d{1,3}(,\d{3})+\.\d+$", s):
        s = s.replace(",", "")
    # 1234,56
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    # 1.234 (milhar sem decimal) — se tiver 1 ponto e 3 dígitos depois, é milhar
    elif s.count(".") == 1 and re.match(r"^\d+\.\d{3}$", s):
        s = s.replace(".", "")
    # 12.5 já ok; 1.234,5 misto
    elif s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def _buscar_valores(padroes: List[str], texto: str) -> List[float]:
    achados: List[float] = []
    for pad in padroes:
        for m in re.finditer(pad, texto, re.IGNORECASE | re.MULTILINE):
            grupos = [g for g in m.groups() if g is not None]
            raw = grupos[-1] if grupos else m.group(0)
            n = _parse_numero_br(raw)
            if n is not None and n > 0:
                achados.append(n)
    return achados


def _eh_energisa(texto: str) -> bool:
    t = texto.lower()
    return "energisa" in t or "energiza" in t


def parsear_fatura(texto: str) -> Dict[str, Any]:
    if not texto or len(texto.strip()) < 15:
        return {
            "consumo_kwh": None,
            "valor_conta": None,
            "tarifa_estimada": None,
            "confianca": "baixa",
            "avisos": [
                "Não foi possível extrair texto da fatura.",
                "Se for PDF da Energisa em modo imagem, instale o Tesseract OCR "
                "(https://github.com/UB-Mannheim/tesseract/wiki) e as libs: "
                "pip install pdfplumber pymupdf pytesseract pillow",
                "Ou preencha consumo e tarifa manualmente no formulário.",
            ],
        }

    avisos: List[str] = []
    t = re.sub(r"[ \t]+", " ", texto)
    t_norm = t.replace("\n", " ")
    # variantes comuns de OCR
    t_norm = (
        t_norm.replace("k Wh", "kWh")
        .replace("kW h", "kWh")
        .replace("kw/h", "kWh")
        .replace("KW H", "kWh")
    )

    energisa = _eh_energisa(texto)
    if energisa:
        avisos.append("Fatura identificada como Energisa.")

    # ---------- Consumo kWh ----------
    padroes_kwh = [
        # Energisa / gerais
        r"consumo\s*(?:de\s*)?(?:energia\s*)?(?:faturado|medido|total|do\s*m[eê]s)?\s*[:=]?\s*([\d\.\,]+)\s*kwh",
        r"energia\s*(?:el[eé]trica|ativa)?\s*(?:kwh)?\s*[:=]?\s*([\d\.\,]+)",
        r"(?:quantidade|qtde|qtd)[^\d]{0,12}([\d\.\,]+)\s*kwh",
        r"([\d\.\,]+)\s*kwh",
        r"kwh\s*[:=]?\s*([\d\.\,]+)",
        r"consumo\s+[:=]?\s*([\d\.\,]+)",
        r"energia\s+ativa[^\d]{0,20}([\d\.\,]+)",
        r"consumo\s+faturado[^\d]{0,15}([\d\.\,]+)",
        # histórico / média
        r"m[eé]dia\s*(?:de\s*)?consumo[^\d]{0,15}([\d\.\,]+)",
        r"hist[oó]rico\s+de\s+consumo.*?([\d\.\,]+)\s*kwh",
    ]
    if energisa:
        padroes_kwh = [
            r"energia\s*el[eé]trica[^\d]{0,30}([\d\.\,]+)",
            r"consumo\s*kwh[^\d]{0,10}([\d\.\,]+)",
            r"([\d\.\,]+)\s*(?:kwh|kw/h)",
            r"quant\.?\s*([\d\.\,]+)",
        ] + padroes_kwh

    candidatos_kwh = _buscar_valores(padroes_kwh, t_norm)
    # faixa típica residencial/comercial
    kwh_ok = [v for v in candidatos_kwh if 15 <= v <= 80000]
    # preferir inteiros (consumo costuma ser inteiro) e valores mais altos razoáveis
    kwh_ok = list(dict.fromkeys(kwh_ok))  # unique preserve order
    kwh_ok.sort(key=lambda x: (0 if abs(x - round(x)) < 0.51 else 1, -x))
    consumo = kwh_ok[0] if kwh_ok else None

    # fallback: maior número seguido de kWh no texto
    if consumo is None:
        todos = re.findall(r"([\d\.\,]+)\s*k\s*w\s*h", t_norm, re.I)
        vals = []
        for raw in todos:
            n = _parse_numero_br(raw)
            if n and 30 <= n <= 50000:
                vals.append(n)
        if vals:
            consumo = max(vals)

    # ---------- Valor total ----------
    padroes_valor = [
        r"total\s*a\s*pagar\s*[:=]?\s*(?:R\$\s*)?([\d\.\,]+)",
        r"valor\s*a\s*pagar\s*[:=]?\s*(?:R\$\s*)?([\d\.\,]+)",
        r"total\s*da\s*(?:fatura|conta)\s*[:=]?\s*(?:R\$\s*)?([\d\.\,]+)",
        r"(?:valor\s*)?total\s*[:=]?\s*(?:R\$\s*)?([\d\.\,]+)",
        r"R\$\s*([\d\.\,]+)\s*(?:total|a\s*pagar)?",
        r"pagar\s*(?:at[eé])?[^\d]{0,25}([\d\.\,]+)",
        r"vencimento[^\d]{0,40}([\d\.\,]+)",
    ]
    if energisa:
        padroes_valor = [
            r"total\s*a\s*pagar[^\d]{0,20}([\d\.\,]+)",
            r"R\$\s*([\d\.\,]+)",
        ] + padroes_valor

    candidatos_val = _buscar_valores(padroes_valor, t_norm)
    vals_ok = [v for v in candidatos_val if 20 <= v <= 500000]
    # total da conta costuma ser um dos maiores valores "em reais" (não tarifa unitária)
    vals_conta = [v for v in vals_ok if v >= 40]
    valor = max(vals_conta) if vals_conta else (max(vals_ok) if vals_ok else None)

    # ---------- Tarifa ----------
    padroes_tarifa = [
        r"(?:tarifa|pre[cç]o\s*unit[aá]rio)\s*[^\d]{0,25}([\d\,\.]+)\s*(?:r\$)?\s*(?:/\s*kwh)?",
        r"([\d\,\.]+)\s*(?:r\$\s*)?/\s*kwh",
        r"(?:tusd|te)\s*[^\d]{0,20}([\d\,\.]+)",
    ]
    candidatos_tar = _buscar_valores(padroes_tarifa, t_norm)
    tar_ok = [v for v in candidatos_tar if 0.12 <= v <= 4.0]
    tarifa = tar_ok[0] if tar_ok else None

    if tarifa is None and consumo and valor and consumo > 0:
        tarifa = round(valor / consumo, 4)
        avisos.append("Tarifa estimada = valor da conta ÷ consumo (média efetiva).")

    confianca = "baixa"
    if consumo and valor:
        confianca = "media"
    if consumo and valor and tarifa:
        confianca = "alta"

    if not consumo:
        avisos.append(
            "Consumo (kWh) não identificado com segurança — confira e preencha manualmente."
        )
    if not valor:
        avisos.append("Valor da conta não identificado com segurança.")

    return {
        "consumo_kwh": round(consumo, 2) if consumo else None,
        "valor_conta": round(valor, 2) if valor else None,
        "tarifa_estimada": round(tarifa, 4) if tarifa else None,
        "confianca": confianca,
        "avisos": avisos,
        "texto_amostra": (texto[:1200] + "…") if len(texto) > 1200 else texto,
        "distribuidora": "Energisa" if energisa else None,
    }


def _diagnostico_libs() -> List[str]:
    msgs = []
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        msgs.append("Falta instalar: pip install pdfplumber")
    try:
        import fitz  # noqa: F401
    except ImportError:
        msgs.append("Falta instalar: pip install pymupdf")
    try:
        import pytesseract  # noqa: F401

        try:
            pytesseract.get_tesseract_version()
        except Exception:
            msgs.append(
                "pytesseract instalado, mas o programa Tesseract não foi encontrado. "
                "No Windows: https://github.com/UB-Mannheim/tesseract/wiki"
            )
    except ImportError:
        msgs.append(
            "Para ler PDF/foto escaneada: pip install pytesseract pillow "
            "e instale o Tesseract no sistema."
        )
    return msgs


def ler_fatura(caminho: str) -> Dict[str, Any]:
    if not caminho or not os.path.isfile(caminho):
        return {
            "consumo_kwh": None,
            "valor_conta": None,
            "tarifa_estimada": None,
            "confianca": "baixa",
            "avisos": ["Arquivo de fatura não encontrado no servidor."],
            "tem_texto": False,
        }

    texto = extrair_texto(caminho)
    resultado = parsear_fatura(texto)
    resultado["caminho"] = caminho
    resultado["tem_texto"] = bool(texto and len(texto.strip()) > 20)

    if not resultado["tem_texto"]:
        extras = _diagnostico_libs()
        for m in extras:
            if m not in resultado["avisos"]:
                resultado["avisos"].append(m)

    return resultado
