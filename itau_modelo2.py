import pymupdf
import pandas as pd
import re


def converter_valor(valor_texto):

    valor_texto = valor_texto.strip()

    valor_texto = valor_texto.replace(".", "")
    valor_texto = valor_texto.replace(",", ".")

    return float(valor_texto)


def ler_itau_modelo2(caminho_pdf):

    documento = pymupdf.open(caminho_pdf)

    registros = []

    # DATA
    padrao_data = re.compile(
        r"^\d{2}/\d{2}/\d{4}$"
    )

    # VALOR
    padrao_valor = re.compile(
        r"^-?\d{1,3}(?:\.\d{3})*,\d{2}$"
    )

    for pagina in documento:

        texto = pagina.get_text("text")

        linhas = [
            linha.strip()
            for linha in texto.splitlines()
            if linha.strip()
        ]

        i = 0

        while i < len(linhas):

            linha = linhas[i]

            # ----------------------------
            # PROCURA UMA DATA
            # ----------------------------

            if not padrao_data.match(linha):
                i += 1
                continue

            data = linha

            # PRECISA TER PELO MENOS
            # HISTÓRICO + VALOR DEPOIS

            if i + 2 >= len(linhas):
                i += 1
                continue

            historico = linhas[i + 1]
            valor_texto = linhas[i + 2]

            # ----------------------------
            # CONFERE SE É VALOR
            # ----------------------------

            if not padrao_valor.match(valor_texto):

                i += 1
                continue

            # ----------------------------
            # IGNORA SALDOS
            # ----------------------------

            historico_upper = historico.upper()

            if "SALDO ANTERIOR" in historico_upper:
                i += 3
                continue

            if "SALDO TOTAL DISPONÍVEL DIA" in historico_upper:
                i += 3
                continue

            # ----------------------------
            # CONVERTE VALOR
            # ----------------------------

            valor = converter_valor(
                valor_texto
            )

            debito = None
            credito = None

            if valor < 0:

                debito = abs(valor)

            else:

                credito = valor

            # ----------------------------
            # SALVA MOVIMENTO
            # ----------------------------

            registros.append({

                "Data": data,

                "Histórico": historico,

                "Débito": debito,

                "Crédito": credito
            })

            i += 3

    documento.close()

    df = pd.DataFrame(
        registros,
        columns=[
            "Data",
            "Histórico",
            "Débito",
            "Crédito"
        ]
    )

    return df