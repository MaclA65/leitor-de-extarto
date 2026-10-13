import io
import os
import re

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

    # --------------------------------------------------------
    # ACEITA:
    #
    # 495,88
    # 13.212,74
    # 600.296,66
    # 0,14
    # 19,86
    # --------------------------------------------------------

    resultado = re.search(
        r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}",
        texto
    )

    if resultado:

        return resultado.group(0)

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

    # --------------------------------------------------------
    # PADRÃO DO CSV:
    #
    # 0,00 -> 0
    # 1,00 -> 1
    # 0,14 -> 0,14
    # 3,11 -> 3,11
    # --------------------------------------------------------

    if valor.endswith(",00"):

        return valor[:-3]

    return valor


# ============================================================
# LOCALIZA O PDF AUTOMATICAMENTE
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


            # ------------------------------------------------
            # PRIORIZA ARQUIVOS COM "APLIC AUT MAIS"
            # ------------------------------------------------

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


    # ========================================================
    # SE NÃO ENCONTROU PELO NOME,
    # PROCURA QUALQUER PDF
    # ========================================================

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
            "Nenhum PDF foi encontrado na pasta do projeto "
            "nem na pasta uploads."
        )


    raise FileNotFoundError(
        "Há mais de um PDF disponível e nenhum contém "
        "'Aplic Aut Mais' no nome."
    )


# ============================================================
# RENDERIZA E GIRA A PÁGINA
# ============================================================

def preparar_pagina(pagina):

    pix = pagina.get_pixmap(
        matrix=pymupdf.Matrix(
            3,
            3
        ),
        alpha=False
    )


    imagem = Image.open(
        io.BytesIO(
            pix.tobytes("png")
        )
    )


    # ========================================================
    # O RELATÓRIO ESTÁ GIRADO
    # ========================================================

    imagem = imagem.rotate(
        270,
        expand=True
    )


    return imagem


# ============================================================
# OCR COMPLETO DA PÁGINA
# ============================================================

def fazer_ocr_pagina(imagem):

    dados = pytesseract.image_to_data(
        imagem,
        lang="por",
        output_type=pytesseract.Output.DATAFRAME
    )


    dados = dados[
        dados["text"].notna()
    ].copy()


    dados["text"] = (
        dados["text"]
        .astype(str)
        .str.strip()
    )


    dados = dados[
        dados["text"] != ""
    ].copy()


    return dados


# ============================================================
# OCR DE UMA COLUNA
# ============================================================

def fazer_ocr_coluna(
    imagem,
    percentual_inicio,
    percentual_fim
):

    largura = imagem.width
    altura = imagem.height


    # ========================================================
    # FAIXA VERTICAL DA TABELA
    # ========================================================

    y_inicio = int(
        altura * 0.19
    )

    y_fim = int(
        altura * 0.86
    )


    # ========================================================
    # FAIXA HORIZONTAL
    # ========================================================

    x_inicio = int(
        largura * percentual_inicio
    )

    x_fim = int(
        largura * percentual_fim
    )


    recorte = imagem.crop(
        (
            x_inicio,
            y_inicio,
            x_fim,
            y_fim
        )
    )


    # ========================================================
    # AMPLIA A COLUNA
    # ========================================================

    recorte = recorte.resize(
        (
            recorte.width * 2,
            recorte.height * 2
        )
    )


    dados = pytesseract.image_to_data(
        recorte,
        lang="por",
        config="--psm 6",
        output_type=pytesseract.Output.DATAFRAME
    )


    dados = dados[
        dados["text"].notna()
    ].copy()


    dados["text"] = (
        dados["text"]
        .astype(str)
        .str.strip()
    )


    dados = dados[
        dados["text"] != ""
    ].copy()


    # ========================================================
    # CONVERTE POSIÇÃO DO RECORTE PARA A PÁGINA ORIGINAL
    # ========================================================

    dados["top_original"] = (
        dados["top"] / 2
        + y_inicio
    )


    return dados


# ============================================================
# ENCONTRA VALOR NA MESMA LINHA DA DATA
# ============================================================

def valor_na_linha(
    dados_coluna,
    y_data,
    tolerancia=8
):

    candidatos = dados_coluna[
        (
            dados_coluna["top_original"]
            >= y_data - tolerancia
        )
        &
        (
            dados_coluna["top_original"]
            <= y_data + tolerancia
        )
    ].copy()


    if candidatos.empty:

        return ""


    candidatos = candidatos.sort_values(
        "left"
    )


    textos = (
        candidatos["text"]
        .astype(str)
        .tolist()
    )


    # ========================================================
    # PRIMEIRO TENTA CADA TOKEN ISOLADO
    # ========================================================

    for texto in textos:

        valor = limpar_valor(
            texto
        )

        if valor:

            return valor


    # ========================================================
    # DEPOIS TENTA A LINHA TODA JUNTA
    # ========================================================

    texto_completo = " ".join(
        textos
    )


    return limpar_valor(
        texto_completo
    )


# ============================================================
# IDENTIFICA DATAS
# ============================================================

def localizar_datas(
    dados,
    largura
):

    resultado = []


    # ========================================================
    # COLUNA DA DATA FICA NO INÍCIO DA TABELA
    # ========================================================

    limite_x = int(
        largura * 0.12
    )


    for _, linha in dados.iterrows():

        texto = str(
            linha["text"]
        ).strip()


        if int(
            linha["left"]
        ) >= limite_x:

            continue


        if not re.fullmatch(
            r"\d{2}/\d{2}/\d{4}",
            texto
        ):

            continue


        resultado.append(
            {
                "Data": texto,

                "top": float(
                    linha["top"]
                )
            }
        )


    resultado = sorted(
        resultado,
        key=lambda item:
        item["top"]
    )


    return resultado


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

        # ====================================================
        # OCR COMPLETO
        # ====================================================

        dados_pagina = fazer_ocr_pagina(
            imagem
        )


        largura = imagem.width


        # ====================================================
        # DATAS
        # ====================================================

        datas = localizar_datas(
            dados_pagina,
            largura
        )


        print(
            "CIBI APLICAÇÃO - DATAS ENCONTRADAS:",
            len(datas)
        )


        if not datas:

            return []


        # ====================================================
        # APLICAÇÕES
        # ====================================================

        coluna_aplicacoes = fazer_ocr_coluna(
            imagem,
            0.15,
            0.215
        )


        # ====================================================
        # VALOR PRINCIPAL RESGATADO
        # ====================================================

        coluna_principal = fazer_ocr_coluna(
            imagem,
            0.275,
            0.345
        )


        # ====================================================
        # IOF
        # ====================================================

        coluna_iof = fazer_ocr_coluna(
            imagem,
            0.395,
            0.45
        )


        # ====================================================
        # IRRF
        # ====================================================

        coluna_irrf = fazer_ocr_coluna(
            imagem,
            0.45,
            0.51
        )


        # ====================================================
        # MONTA REGISTROS
        # ====================================================

        registros = []


        for item in datas:

            data = item[
                "Data"
            ]

            y = item[
                "top"
            ]


            aplicacao = valor_na_linha(
                coluna_aplicacoes,
                y
            )


            principal = valor_na_linha(
                coluna_principal,
                y
            )


            iof = valor_na_linha(
                coluna_iof,
                y
            )


            irrf = valor_na_linha(
                coluna_irrf,
                y
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

                    "aplicações": aplicacao,

                    "valor principal resgatado": principal,

                    "iof": iof,

                    "irrf": irrf
                }
            )


        return registros


    finally:

        imagem.close()


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
    # DATAFRAME
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
    # REMOVE LINHAS COMPLETAMENTE VAZIAS
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


    # ========================================================
    # MANTÉM A ORDEM ORIGINAL
    # ========================================================

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


            # =================================================
            # MESMO NOME DO PDF
            # =================================================

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