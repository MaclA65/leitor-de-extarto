import fitz
import re
import pandas as pd


def converter_valor(texto):
    texto = texto.strip()

    negativo = texto.endswith("-")

    texto = texto.replace("-", "")
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

    valor = float(texto)

    return -valor if negativo else valor


def ler_extrato_itau(caminho_pdf):

    documento = fitz.open(caminho_pdf)

    linhas = []

    for pagina in documento:
        texto = pagina.get_text()

        for linha in texto.splitlines():
            linha = linha.strip()

            if linha:
                linhas.append(linha)

    registros = []

    data_atual = None
    historico_atual = None

    lendo_movimento = False

    padrao_data = re.compile(r"^\d{2}/\d{2}$")

    padrao_valor = re.compile(
        r"^\d{1,3}(?:\.\d{3})*,\d{2}-?$"
    )

    padrao_percentual = re.compile(
        r"^\d+(?:,\d+)?%$"
    )

    for linha in linhas:

        # COMEÇA A LEITURA DO MOVIMENTO
        if "Conta Corrente | Movimentação" in linha:
            lendo_movimento = True
            historico_atual = None
            continue

        # PARA QUANDO CHEGAR NAS APLICAÇÕES
        if "Conta Corrente | Aplicações Automáticas" in linha:
            lendo_movimento = False
            break

        if not lendo_movimento:
            continue

        # IGNORA CABEÇALHOS
        if linha in [
            "data",
            "descrição",
            "entradas R$",
            "saídas R$",
            "saldo R$",
            "saldo  R$",
            "(créditos)",
            "(débitos)"
        ]:
            continue

        # IGNORA PERCENTUAIS
        if padrao_percentual.match(linha):
            continue

        # IGNORA TOTAIS E SALDOS
        linha_minuscula = linha.lower()

        if (
            linha_minuscula == "total"
            or linha_minuscula.startswith("saldo anterior")
            or linha_minuscula.startswith("saldo final")
            or linha_minuscula.startswith("saldo em c/c")
            or linha_minuscula.startswith("saldo aplic aut mais")
        ):
            historico_atual = None
            continue

        # DATA
        if padrao_data.match(linha):
            data_atual = linha
            historico_atual = None
            continue

        # VALOR
        if padrao_valor.match(linha) and historico_atual:

            valor = converter_valor(linha)

            debito = None
            credito = None

            if valor < 0:
                debito = abs(valor)
            else:
                credito = valor

            registros.append({
                "Data": data_atual,
                "Histórico": historico_atual,
                "Débito": debito,
                "Crédito": credito
            })

            historico_atual = None
            continue

        # IGNORA RODAPÉ
        if linha.startswith("054966"):
            continue

        # GUARDA O HISTÓRICO
        historico_atual = linha

    return pd.DataFrame(registros)