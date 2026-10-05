import pymupdf
import pandas as pd
import re
from datetime import datetime


def converter_valor(texto):

    texto = texto.strip()
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

    return float(texto)


def ler_itau_aplicacao(caminho_pdf):

    documento = pymupdf.open(caminho_pdf)

    registros = []

    ano = None
    iniciou_aplicacao = False
    terminou_aplicacao = False

    # DESCOBRE O ANO
    for pagina in documento:

        texto = pagina.get_text("text")

        resultado_ano = re.search(
            r"\d{2}/\d{2}/(\d{4})",
            texto
        )

        if resultado_ano:
            ano = resultado_ano.group(1)
            break

    if ano is None:
        ano = str(datetime.now().year)

    # LÊ AS PÁGINAS
    for pagina in documento:

        if terminou_aplicacao:
            break

        texto = pagina.get_text(
            "text",
            sort=True
        )

        linhas = [
            linha.strip()
            for linha in texto.splitlines()
            if linha.strip()
        ]

        for linha in linhas:

            linha_upper = linha.upper()

            # COMEÇA NA TABELA DE APLICAÇÕES
            if (
                "MOVIMENTAÇÃO - APLICAÇÕES/RESGATES"
                in linha_upper
                or
                "MOVIMENTACAO - APLICACOES/RESGATES"
                in linha_upper
            ):

                iniciou_aplicacao = True
                continue

            if not iniciou_aplicacao:
                continue

            # TERMINA A SEÇÃO
            if (
                "CONTA CORRENTE | CHEQUE ESPECIAL"
                in linha_upper
            ):

                terminou_aplicacao = True
                break

            # IGNORA TOTAL
            if linha_upper.startswith("TOTAL "):
                continue

            # PROCURA:
            # DATA + APLICAÇÃO + RESGATE
            resultado = re.match(
                r"^(\d{2}/\d{2})\s+"
                r"([\d\.]+,\d{2})\s+"
                r"([\d\.]+,\d{2})",
                linha
            )

            if not resultado:
                continue

            data = resultado.group(1)
            aplicacao_texto = resultado.group(2)
            resgate_texto = resultado.group(3)

            aplicacao = converter_valor(
                aplicacao_texto
            )

            resgate = converter_valor(
                resgate_texto
            )

            data_completa = (
                f"{data}/{ano}"
            )

            debito = None
            credito = None

            # APLICAÇÃO = DÉBITO
            if aplicacao != 0:
                debito = aplicacao

            # RESGATE = CRÉDITO
            if resgate != 0:
                credito = resgate

            registros.append({
                "Data": data_completa,
                "Débito": debito,
                "Crédito": credito
            })

    documento.close()

    df = pd.DataFrame(
        registros,
        columns=[
            "Data",
            "Débito",
            "Crédito"
        ]
    )

    return df