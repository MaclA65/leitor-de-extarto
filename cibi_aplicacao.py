import io
import os
import re

# ============================================================
# LIMITA O TESSERACT A 1 THREAD
# ============================================================

os.environ["OMP_THREAD_LIMIT"] = "1"

import pandas as pd
import pymupdf
import pytesseract

from PIL import Image
from pathlib import Path


# ============================================================
# TESSERACT WINDOWS
# ============================================================

CAMINHO_TESSERACT_WINDOWS = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if CAMINHO_TESSERACT_WINDOWS.exists():

    pytesseract.pytesseract.tesseract_cmd = str(
        CAMINHO_TESSERACT_WINDOWS
    )


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ESCALA_RENDER = 1.5


# ============================================================
# NORMALIZA TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    return (
        str(texto)
        .strip()
        .lower()
    )


# ============================================================
# LIMPA VALOR MONETÁRIO
# ============================================================

def limpar_valor(valor):

    if valor is None:
        return ""

    texto = str(valor).strip()

    if not texto:
        return ""

    texto = (
        texto
        .replace(" ", "")
        .replace("R$", "")
    )


    # ========================================================
    # PADRÃO BRASILEIRO
    # ========================================================

    resultado = re.search(
        r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}",
        texto
    )

    if resultado:

        return resultado.group(0)


    # ========================================================
    # OCR PODE TROCAR VÍRGULA POR PONTO
    # ========================================================

    resultado = re.search(
        r"\d+\.\d{2}",
        texto
    )

    if resultado:

        numero = resultado.group(0)

        inteiro, centavos = numero.rsplit(
            ".",
            1
        )

        return (
            inteiro
            + ","
            + centavos
        )


    return ""


# ============================================================
# FORMATA IOF / IRRF
# ============================================================

def formatar_imposto(valor):

    valor = limpar_valor(
        valor
    )

    if not valor:
        return ""

    if valor.endswith(",00"):

        return valor[:-3]

    return valor


# ============================================================
# LOCALIZA PDF PARA TESTE
# ============================================================

def localizar_pdf_teste():

    pastas = [
        Path("."),
        Path("uploads")
    ]

    candidatos = []


    for pasta in pastas:

        if not pasta.exists():
            continue


        for arquivo in pasta.iterdir():

            if not arquivo.is_file():
                continue

            if arquivo.suffix.lower() != ".pdf":
                continue


            nome = normalizar_texto(
                arquivo.name
            )


            if (
                "aplic aut mais" in nome
                or
                "aplic_aut_mais" in nome
                or
                "aplicacao" in nome
            ):

                candidatos.append(
                    arquivo
                )


    if candidatos:

        candidatos = sorted(
            candidatos,
            key=lambda arquivo:
            arquivo.stat().st_mtime,
            reverse=True
        )

        return str(
            candidatos[0]
        )


    todos_pdfs = []


    for pasta in pastas:

        if not pasta.exists():
            continue


        for arquivo in pasta.iterdir():

            if (
                arquivo.is_file()
                and arquivo.suffix.lower() == ".pdf"
            ):

                todos_pdfs.append(
                    arquivo
                )


    if len(todos_pdfs) == 1:

        return str(
            todos_pdfs[0]
        )


    if not todos_pdfs:

        raise FileNotFoundError(
            "Nenhum PDF encontrado."
        )


    raise FileNotFoundError(
        "Há vários PDFs disponíveis e nenhum "
        "contém 'Aplic Aut Mais' no nome."
    )


# ============================================================
# PREPARA PÁGINA
# ============================================================

def preparar_pagina(pagina):

    # ========================================================
    # RENDERIZA EM 1.5X
    #
    # Antes usávamos 2x / 3x.
    # ========================================================

    pix = pagina.get_pixmap(
        matrix=pymupdf.Matrix(
            ESCALA_RENDER,
            ESCALA_RENDER
        ),
        alpha=False
    )


    imagem = Image.open(
        io.BytesIO(
            pix.tobytes("png")
        )
    )


    # ========================================================
    # GIRA O RELATÓRIO
    # ========================================================

    imagem = imagem.rotate(
        270,
        expand=True
    )


    # ========================================================
    # CONVERTE PARA CINZA
    #
    # NÃO RECORTA MAIS A PÁGINA.
    # ========================================================

    imagem_cinza = imagem.convert(
        "L"
    )

    imagem.close()


    return imagem_cinza


# ============================================================
# OCR ÚNICO
# ============================================================

def fazer_ocr_unico(imagem):

    dados = pytesseract.image_to_data(
        imagem,
        lang="por",
        config="--psm 6",
        output_type=pytesseract.Output.DICT
    )


    tokens = []


    quantidade = len(
        dados["text"]
    )


    for i in range(
        quantidade
    ):

        texto = str(
            dados["text"][i]
        ).strip()


        if not texto:
            continue


        try:

            left = int(
                dados["left"][i]
            )

            top = int(
                dados["top"][i]
            )

            width = int(
                dados["width"][i]
            )

            block = int(
                dados["block_num"][i]
            )

            par = int(
                dados["par_num"][i]
            )

            line = int(
                dados["line_num"][i]
            )

        except Exception:

            continue


        tokens.append(
            {
                "texto": texto,
                "left": left,
                "right": left + width,
                "top": top,
                "block": block,
                "par": par,
                "line": line
            }
        )


    return tokens


# ============================================================
# AGRUPA TOKENS POR LINHA
# ============================================================

def agrupar_linhas(tokens):

    grupos = {}


    for token in tokens:

        chave = (
            token["block"],
            token["par"],
            token["line"]
        )


        if chave not in grupos:

            grupos[chave] = []


        grupos[chave].append(
            token
        )


    linhas = []


    for palavras in grupos.values():

        palavras = sorted(
            palavras,
            key=lambda item:
            item["left"]
        )


        if not palavras:
            continue


        top = sum(
            palavra["top"]
            for palavra in palavras
        ) / len(palavras)


        texto = " ".join(
            palavra["texto"]
            for palavra in palavras
        )


        linhas.append(
            {
                "texto": texto,
                "top": top,
                "palavras": palavras
            }
        )


    linhas = sorted(
        linhas,
        key=lambda item:
        item["top"]
    )


    return linhas


# ============================================================
# LOCALIZA DATAS
# ============================================================

def localizar_datas(
    linhas,
    largura
):

    datas = []


    # ========================================================
    # DATA FICA NA PRIMEIRA PARTE DA TABELA
    # ========================================================

    limite_x = (
        largura
        * 0.15
    )


    for linha in linhas:

        for palavra in linha[
            "palavras"
        ]:

            texto = palavra[
                "texto"
            ].strip()


            if palavra[
                "left"
            ] > limite_x:

                continue


            # =================================================
            # FORMATO NORMAL
            #
            # 02/06/2026
            # =================================================

            if re.fullmatch(
                r"\d{2}/\d{2}/\d{4}",
                texto
            ):

                datas.append(
                    {
                        "Data": texto,
                        "top": linha["top"]
                    }
                )

                break


    return datas


# ============================================================
# LOCALIZA LINHA DA DATA
# ============================================================

def localizar_linha_data(
    linhas,
    y_data,
    tolerancia=12
):

    melhor = None
    menor_distancia = None


    for linha in linhas:

        distancia = abs(
            linha["top"]
            - y_data
        )


        if distancia > tolerancia:

            continue


        if (
            menor_distancia is None
            or distancia < menor_distancia
        ):

            menor_distancia = distancia
            melhor = linha


    return melhor


# ============================================================
# EXTRAI VALOR POR FAIXA HORIZONTAL
# ============================================================

def extrair_valor_faixa(
    linha,
    largura,
    percentual_inicio,
    percentual_fim
):

    if linha is None:

        return ""


    x_inicio = (
        largura
        * percentual_inicio
    )

    x_fim = (
        largura
        * percentual_fim
    )


    textos = []


    for palavra in linha[
        "palavras"
    ]:

        centro = (
            palavra["left"]
            + palavra["right"]
        ) / 2


        if (
            centro >= x_inicio
            and centro < x_fim
        ):

            textos.append(
                palavra["texto"]
            )


    if not textos:

        return ""


    texto = " ".join(
        textos
    )


    return limpar_valor(
        texto
    )


# ============================================================
# LÊ UMA PÁGINA
# ============================================================

def ler_pagina_aplicacao(
    pagina
):

    imagem = preparar_pagina(
        pagina
    )


    try:

        largura = imagem.width


        print(
            "CIBI APLICAÇÃO - TAMANHO DA IMAGEM:",
            imagem.width,
            "x",
            imagem.height
        )


        # ====================================================
        # APENAS UM OCR
        # ====================================================

        tokens = fazer_ocr_unico(
            imagem
        )


        print(
            "CIBI APLICAÇÃO - TOKENS OCR:",
            len(tokens)
        )


    finally:

        imagem.close()


    # ========================================================
    # AGRUPA LINHAS
    # ========================================================

    linhas = agrupar_linhas(
        tokens
    )


    # ========================================================
    # LOCALIZA DATAS
    # ========================================================

    datas = localizar_datas(
        linhas,
        largura
    )


    print(
        "CIBI APLICAÇÃO - DATAS ENCONTRADAS:",
        len(datas)
    )


    registros = []


    # ========================================================
    # PROCESSA CADA DATA
    # ========================================================

    for item in datas:

        data = item[
            "Data"
        ]

        y_data = item[
            "top"
        ]


        linha = localizar_linha_data(
            linhas,
            y_data
        )


        if linha is None:

            continue


        # ====================================================
        # APLICAÇÕES
        # ====================================================

        aplicacao = extrair_valor_faixa(
            linha,
            largura,
            0.15,
            0.23
        )


        # ====================================================
        # PRINCIPAL RESGATADO
        # ====================================================

        principal = extrair_valor_faixa(
            linha,
            largura,
            0.26,
            0.36
        )


        # ====================================================
        # IOF
        # ====================================================

        iof = extrair_valor_faixa(
            linha,
            largura,
            0.39,
            0.46
        )


        # ====================================================
        # IRRF
        # ====================================================

        irrf = extrair_valor_faixa(
            linha,
            largura,
            0.46,
            0.53
        )


        iof = formatar_imposto(
            iof
        )


        irrf = formatar_imposto(
            irrf
        )


        registros.append(
            {
                "DATA": data,

                "aplicações":
                aplicacao,

                "valor principal resgatado":
                principal,

                "iof":
                iof,

                "irrf":
                irrf
            }
        )


    return registros


# ============================================================
# LEITOR PRINCIPAL
# ============================================================

def ler_cibi_aplicacao(
    caminho_pdf
):

    if not os.path.exists(
        caminho_pdf
    ):

        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_pdf}"
        )


    documento = pymupdf.open(
        caminho_pdf
    )


    registros = []


    try:

        for numero_pagina, pagina in enumerate(
            documento,
            start=1
        ):

            print(
                "CIBI APLICAÇÃO - LENDO PÁGINA:",
                numero_pagina
            )


            registros_pagina = (
                ler_pagina_aplicacao(
                    pagina
                )
            )


            registros.extend(
                registros_pagina
            )


    finally:

        documento.close()


    # ========================================================
    # DATAFRAME FINAL
    # ========================================================

    df = pd.DataFrame(
        registros,
        columns=[
            "DATA",
            "aplicações",
            "valor principal resgatado",
            "iof",
            "irrf"
        ]
    )


    if df.empty:

        return df


    # ========================================================
    # REMOVE LINHAS SEM VALOR
    # ========================================================

    df = df[
        ~(
            (df["aplicações"] == "")
            &
            (
                df[
                    "valor principal resgatado"
                ]
                == ""
            )
            &
            (df["iof"] == "")
            &
            (df["irrf"] == "")
        )
    ].copy()


    df = df.reset_index(
        drop=True
    )


    return df


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    print(
        "INICIANDO CIBI APLICAÇÃO..."
    )


    try:

        caminho_pdf = localizar_pdf_teste()


        print(
            "PDF LOCALIZADO:"
        )

        print(
            caminho_pdf
        )


        df = ler_cibi_aplicacao(
            caminho_pdf
        )


        print(
            "\n=============================="
        )

        print(
            "RESULTADO"
        )

        print(
            "==============================\n"
        )


        if df.empty:

            print(
                "Nenhuma movimentação encontrada."
            )


        else:

            print(
                df.to_string(
                    index=False
                )
            )


            nome_pdf = Path(
                caminho_pdf
            )


            nome_saida = (
                nome_pdf.stem
                + ".csv"
            )


            df.to_csv(
                nome_saida,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )


            print(
                "\nARQUIVO GERADO:"
            )

            print(
                nome_saida
            )


    except Exception as erro:

        print(
            "\nERRO:"
        )

        print(
            erro
        )