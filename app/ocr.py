"""Texto a partir do arquivo enviado.

.txt passa direto (útil para testes e para notas já em texto). Imagens usam
Tesseract em português, instalado na imagem Docker.
"""
from __future__ import annotations

import io


class FormatoNaoSuportado(ValueError):
    pass


def texto_do_arquivo(nome: str, conteudo: bytes) -> str:
    nome = nome.lower()
    if nome.endswith(".txt"):
        return conteudo.decode("utf-8", errors="replace")
    if nome.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            raise FormatoNaoSuportado("Instale o extra [ocr] para ler imagens") from e
        return pytesseract.image_to_string(Image.open(io.BytesIO(conteudo)), lang="por")
    raise FormatoNaoSuportado(f"Formato não suportado: {nome}")
