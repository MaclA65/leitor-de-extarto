import fitz
import re
import pandas as pd


# ============================================================
# CONVERTE VALOR
# ============================================================

def converter_valor(texto):

    texto = texto.strip()

    negativo = texto.endswith("-")

    texto = texto.replace("-", "")
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

    valor = float(texto)

    return -valor if negativo else valor


# ============================================================
# LEITOR ITAÚ
# ============================================================

def ler_extrato_itau(caminho_pdf):

    documento = fitz.open(
        caminho_pdf
    )

    linhas = []

    # ========================================================
    # EXTRAI TODO O TEXTO DO PDF
    # ========================================================

    for pagina in documento:

        texto = pagina.get_text()

        for linha in texto.splitlines():

            linha = linha.strip()

            if linha:
                linhas.append(
                    linha
                )

    documento.close()

    # ========================================================
    # VARIÁVEIS
    # ========================================================

    registros = []

    data_atual = None
    historico_atual = None

    lendo_movimento = False

    # ========================================================
    # PADRÕES
    # ========================================================

    padrao_data = re.compile(
        r"^\d{2}/\d{2}$"
    )

    padrao_valor = re.compile(
        r"^\d{1,3}(?:\.\d{3})*,\d{2}-?$"
    )

    padrao_percentual = re.compile(
        r"^\d+(?:,\d+)?%$"
    )

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    for linha in linhas:

        linha_minuscula = (
            linha
            .lower()
            .strip()
        )

        # ====================================================
        # INÍCIO DA MOVIMENTAÇÃO
        # ====================================================

        if (
            "conta corrente | movimentação"
            in linha_minuscula
            or
            "conta corrente | movimentacao"
            in linha_minuscula
        ):

            lendo_movimento = True

            data_atual = None
            historico_atual = None

            continue

        # ====================================================
        # SE AINDA NÃO COMEÇOU A MOVIMENTAÇÃO
        # ====================================================

        if not lendo_movimento:
            continue

        # ====================================================
        # FIM DA MOVIMENTAÇÃO
        #
        # IMPORTANTE:
        #
        # Depois daqui o Itaú pode apresentar:
        #
        # Débitos automáticos efetuados
        # Cheque Especial
        # Aplicações automáticas
        #
        # Essas áreas NÃO fazem parte do CSV da movimentação.
        # ====================================================

        if linha_minuscula.startswith(
            "saldo final"
        ):

            historico_atual = None
            lendo_movimento = False

            break

        # ====================================================
        # TRAVAS ADICIONAIS
        # ====================================================

        if (
            "débitos automáticos efetuados"
            in linha_minuscula
            or
            "debitos automaticos efetuados"
            in linha_minuscula
        ):

            historico_atual = None
            lendo_movimento = False

            break

        if (
            "cheque especial"
            in linha_minuscula
        ):

            historico_atual = None
            lendo_movimento = False

            break

        if (
            "conta corrente | aplicações automáticas"
            in linha_minuscula
            or
            "conta corrente | aplicacoes automaticas"
            in linha_minuscula
        ):

            historico_atual = None
            lendo_movimento = False

            break

        # ====================================================
        # IGNORA CABEÇALHOS
        # ====================================================

        if linha_minuscula in [
            "data",
            "descrição",
            "descricao",
            "entradas r$",
            "saídas r$",
            "saidas r$",
            "saldo r$",
            "saldo  r$",
            "(créditos)",
            "(creditos)",
            "(débitos)",
            "(debitos)"
        ]:

            continue

        # ====================================================
        # IGNORA PERCENTUAIS
        # ====================================================

        if padrao_percentual.match(
            linha
        ):

            continue

        # ====================================================
        # IGNORA TOTAIS E SALDOS INTERMEDIÁRIOS
        # ====================================================

        if (
            linha_minuscula == "total"
            or linha_minuscula.startswith(
                "saldo anterior"
            )
            or linha_minuscula.startswith(
                "saldo em c/c"
            )
            or linha_minuscula.startswith(
                "saldo aplic aut mais"
            )
        ):

            historico_atual = None

            continue

        # ====================================================
        # DATA
        # ====================================================

        if padrao_data.match(
            linha
        ):

            data_atual = linha

            historico_atual = None

            continue

        # ====================================================
        # VALOR
        # ====================================================

        if (
            padrao_valor.match(
                linha
            )
            and historico_atual
        ):

            valor = converter_valor(
                linha
            )

            debito = None
            credito = None

            if valor < 0:

                debito = abs(
                    valor
                )

            else:

                credito = valor

            registros.append(
                {
                    "Data": data_atual,
                    "Histórico": historico_atual,
                    "Débito": debito,
                    "Crédito": credito
                }
            )

            historico_atual = None

            continue

        # ====================================================
        # IGNORA RODAPÉ
        # ====================================================

        if linha.startswith(
            "054966"
        ):

            continue

        # ====================================================
        # GUARDA HISTÓRICO
        # ====================================================

        historico_atual = linha

    # ========================================================
    # RESULTADO
    # ========================================================

    return pd.DataFrame(
        registros
    )