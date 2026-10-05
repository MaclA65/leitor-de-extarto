import pymupdf
import pandas as pd
import re
from datetime import datetime


def converter_valor(texto):

    texto = texto.strip()
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

    return float(texto)


def ler_bradesco_unificado(caminho_pdf):

    documento = pymupdf.open(caminho_pdf)

    registros = []

    data_atual = None
    ano = None

    # =========================================
    # DESCOBRE O ANO DO EXTRATO
    # =========================================

    for pagina in documento:

        texto_pagina = pagina.get_text("text")

        if ano is None:

            resultado_ano = re.search(
                r"\d{2}/\d{2}/(\d{4})",
                texto_pagina
            )

            if resultado_ano:
                ano = resultado_ano.group(1)

    if ano is None:
        ano = str(datetime.now().year)


    # =========================================
    # CONTROLE DA LEITURA
    # =========================================

    iniciou_movimentacao = False
    terminou_movimentacao = False


    # =========================================
    # PROCESSA AS PÁGINAS
    # =========================================

    for numero_pagina, pagina in enumerate(documento):

        if terminou_movimentacao:
            break

        palavras = pagina.get_text("words")

        linhas = {}


        # =========================================
        # AGRUPA AS PALAVRAS POR LINHA
        # =========================================

        for palavra in palavras:

            x0, y0, x1, y1, texto = palavra[:5]

            chave_y = round(y0, 1)

            chave_encontrada = None

            for chave_existente in linhas:

                if abs(chave_existente - chave_y) < 2:

                    chave_encontrada = chave_existente
                    break

            if chave_encontrada is None:

                linhas[chave_y] = []
                chave_encontrada = chave_y

            linhas[chave_encontrada].append(
                (x0, texto)
            )


        # =========================================
        # ORDENA AS LINHAS
        # =========================================

        linhas_ordenadas = sorted(
            linhas.items(),
            key=lambda item: item[0]
        )


        # =========================================
        # ANALISA AS LINHAS
        # =========================================

        for y, palavras_linha in linhas_ordenadas:

            palavras_linha = sorted(
                palavras_linha,
                key=lambda item: item[0]
            )

            texto_linha = " ".join(
                texto
                for x, texto in palavras_linha
            ).strip()

            texto_upper = texto_linha.upper()


            # =========================================
            # COMEÇA NA MOVIMENTAÇÃO
            # =========================================

            if "DEMONSTRATIVO DA MOVIMENTAÇÃO" in texto_upper:

                iniciou_movimentacao = True
                continue


            if not iniciou_movimentacao:
                continue


            # =========================================
            # PARA ANTES DA ÁREA DE INVESTIMENTOS
            # =========================================

            sinais_investimento = [
                "INVESTIMENTOS",
                "CDB BRADESCO",
                "INVEST FÁCIL BRADESCO",
                "INVEST FACIL BRADESCO",
                "DATA APLICAÇÃO",
                "DATA APLICACAO",
                "VALOR PRINCIPAL",
                "DATA VENCIMENTO",
                "RESGATE BRUTO",
                "RENDA TRIBUTÁVEL",
                "RENDA TRIBUTAVEL"
            ]

            if any(
                sinal in texto_upper
                for sinal in sinais_investimento
            ):

                terminou_movimentacao = True
                break


            # =========================================
            # IGNORA CABEÇALHOS
            # =========================================

            if (
                "EXTRATO UNIFICADO" in texto_upper
                or "DATA HISTÓRICO" in texto_upper
                or texto_upper.startswith("MOD.:")
            ):

                continue


            # =========================================
            # SEPARA AS COLUNAS
            # =========================================

            coluna_data = []
            coluna_historico = []
            coluna_credito = []
            coluna_debito = []


            for x, texto in palavras_linha:

                # DATA
                if x < 75:

                    coluna_data.append(texto)

                # HISTÓRICO
                elif 75 <= x < 270:

                    coluna_historico.append(texto)

                # DOCUMENTO:
                # 270 até 330
                # não precisamos

                # CRÉDITO
                elif 330 <= x < 425:

                    coluna_credito.append(texto)

                # DÉBITO
                elif 425 <= x < 515:

                    coluna_debito.append(texto)

                # SALDO:
                # acima de 515
                # ignorado


            # =========================================
            # MONTA OS CAMPOS
            # =========================================

            data_texto = " ".join(
                coluna_data
            ).strip()

            historico = " ".join(
                coluna_historico
            ).strip()

            credito_texto = " ".join(
                coluna_credito
            ).strip()

            debito_texto = " ".join(
                coluna_debito
            ).strip()


            # =========================================
            # DATA
            # =========================================

            if re.fullmatch(
                r"\d{2}/\d{2}",
                data_texto
            ):

                data_atual = (
                    f"{data_texto}/{ano}"
                )


            # =========================================
            # IGNORA SALDOS E TOTAIS
            # =========================================

            historico_upper = historico.upper()

            if historico_upper == "SALDO ANTERIOR":
                continue

            if historico_upper == "TOTAL":
                continue


            # =========================================
            # IDENTIFICA CRÉDITO
            # =========================================

            tem_credito = bool(
                re.fullmatch(
                    r"\d{1,3}(?:\.\d{3})*,\d{2}",
                    credito_texto
                )
            )


            # =========================================
            # IDENTIFICA DÉBITO
            # =========================================

            tem_debito = bool(
                re.fullmatch(
                    r"\d{1,3}(?:\.\d{3})*,\d{2}",
                    debito_texto
                )
            )


            # =========================================
            # MOVIMENTAÇÃO PRINCIPAL
            # =========================================

            if historico and (
                tem_credito or tem_debito
            ):

                credito = None
                debito = None

                if tem_credito:

                    credito = converter_valor(
                        credito_texto
                    )

                if tem_debito:

                    debito = converter_valor(
                        debito_texto
                    )

                registros.append({
                    "Data": data_atual,
                    "Histórico": historico,
                    "Crédito": credito,
                    "Débito": debito
                })

                continue


            # =========================================
            # COMPLEMENTO DO HISTÓRICO
            # =========================================

            if (
                historico
                and registros
                and not tem_credito
                and not tem_debito
            ):

                ignorar_complemento = [
                    "CONTA-CORRENTE",
                    "DATA",
                    "HISTÓRICO",
                    "DOCTO",
                    "CRÉDITO",
                    "DÉBITO",
                    "SALDO"
                ]

                if historico_upper not in ignorar_complemento:

                    registros[-1]["Histórico"] += (
                        " " + historico
                    )


    documento.close()


    # =========================================
    # DATAFRAME FINAL
    # =========================================

    df = pd.DataFrame(
        registros,
        columns=[
            "Data",
            "Histórico",
            "Crédito",
            "Débito"
        ]
    )

    return df