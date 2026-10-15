import fitz
import os
import re
import unicodedata

import pandas as pd


# ============================================================
# MESES EM PORTUGUÊS
# ============================================================

MESES = {
    "jan": 1,
    "janeiro": 1,

    "fev": 2,
    "fevereiro": 2,

    "mar": 3,
    "marco": 3,
    "março": 3,

    "abr": 4,
    "abril": 4,

    "mai": 5,
    "maio": 5,

    "jun": 6,
    "junho": 6,

    "jul": 7,
    "julho": 7,

    "ago": 8,
    "agosto": 8,

    "set": 9,
    "setembro": 9,

    "out": 10,
    "outubro": 10,

    "nov": 11,
    "novembro": 11,

    "dez": 12,
    "dezembro": 12,
}


# ============================================================
# NORMALIZA TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    return texto


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
# PROCURA O ANO DO EXTRATO
# ============================================================

def localizar_ano_extrato(
    linhas,
    caminho_pdf
):

    anos = []


    # ========================================================
    # 1. PROCURA ANO DENTRO DO PRÓPRIO PDF
    #
    # Exemplos:
    # 01/08/2026
    # Agosto 2026
    # Período 01/08/2026 a 31/08/2026
    # ========================================================

    for linha in linhas:

        encontrados = re.findall(
            r"\b(20\d{2})\b",
            str(linha)
        )

        for ano in encontrados:

            anos.append(
                int(ano)
            )


    if anos:

        # ====================================================
        # PEGA O ANO QUE MAIS APARECE NO DOCUMENTO
        # ====================================================

        return max(
            set(anos),
            key=anos.count
        )


    # ========================================================
    # 2. SE NÃO ACHOU NO PDF,
    # PROCURA NO NOME DO ARQUIVO
    #
    # Exemplos:
    # SERVA 08.2026.pdf
    # EXTRATO_SERVA_2027.pdf
    # ========================================================

    nome_arquivo = os.path.basename(
        caminho_pdf
    )


    encontrado = re.search(
        r"\b(20\d{2})\b",
        nome_arquivo
    )


    if encontrado:

        return int(
            encontrado.group(1)
        )


    # ========================================================
    # NÃO INVENTA O ANO
    # ========================================================

    raise ValueError(
        "Não foi possível identificar o ano "
        "do extrato. O PDF ou o nome do arquivo "
        "deve conter o ano, por exemplo 2026."
    )


# ============================================================
# FORMATA DATA DO EXTRATO
# ============================================================

def formatar_data_extrato(
    texto,
    ano
):

    texto = str(
        texto
    ).strip()


    # ========================================================
    # DD/MM
    #
    # 03/08
    # ========================================================

    resultado = re.fullmatch(
        r"(\d{1,2})/(\d{1,2})",
        texto
    )


    if resultado:

        dia = int(
            resultado.group(1)
        )

        mes = int(
            resultado.group(2)
        )


        return (
            f"{dia:02d}/"
            f"{mes:02d}/"
            f"{ano}"
        )


    # ========================================================
    # DD/MM/AAAA
    #
    # SE JÁ VIER COMPLETA, MANTÉM
    # ========================================================

    resultado = re.fullmatch(
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
        texto
    )


    if resultado:

        dia = int(
            resultado.group(1)
        )

        mes = int(
            resultado.group(2)
        )

        ano_data = int(
            resultado.group(3)
        )


        return (
            f"{dia:02d}/"
            f"{mes:02d}/"
            f"{ano_data}"
        )


    # ========================================================
    # DD/MÊS
    #
    # Exemplos:
    # 03/ago
    # 03/agosto
    # ========================================================

    resultado = re.fullmatch(
        r"(\d{1,2})/([A-Za-zÀ-ÿ]+)",
        texto
    )


    if resultado:

        dia = int(
            resultado.group(1)
        )


        mes_texto = normalizar_texto(
            resultado.group(2)
        )


        if mes_texto not in MESES:

            raise ValueError(
                f"Mês não reconhecido na data: {texto}"
            )


        mes = MESES[
            mes_texto
        ]


        return (
            f"{dia:02d}/"
            f"{mes:02d}/"
            f"{ano}"
        )


    # ========================================================
    # DD MÊS
    #
    # Exemplos:
    # 03 ago
    # 03 agosto
    # ========================================================

    resultado = re.fullmatch(
        r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)",
        texto
    )


    if resultado:

        dia = int(
            resultado.group(1)
        )


        mes_texto = normalizar_texto(
            resultado.group(2)
        )


        if mes_texto not in MESES:

            raise ValueError(
                f"Mês não reconhecido na data: {texto}"
            )


        mes = MESES[
            mes_texto
        ]


        return (
            f"{dia:02d}/"
            f"{mes:02d}/"
            f"{ano}"
        )


    # ========================================================
    # SE NÃO RECONHECEU
    # ========================================================

    return texto


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
    # IDENTIFICA ANO
    # ========================================================

    ano_extrato = localizar_ano_extrato(
        linhas,
        caminho_pdf
    )


    print(
        "ITAÚ - ANO IDENTIFICADO:",
        ano_extrato
    )


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

    padrao_data_numerica = re.compile(
        r"^\d{1,2}/\d{1,2}$"
    )


    padrao_data_completa = re.compile(
        r"^\d{1,2}/\d{1,2}/\d{4}$"
    )


    padrao_data_mes_texto = re.compile(
        r"^\d{1,2}/[A-Za-zÀ-ÿ]+$"
    )


    padrao_data_mes_texto_espaco = re.compile(
        r"^\d{1,2}\s+[A-Za-zÀ-ÿ]+$"
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
        # SE AINDA NÃO COMEÇOU
        # ====================================================

        if not lendo_movimento:

            continue


        # ====================================================
        # FIM DA MOVIMENTAÇÃO
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
        # IGNORA TOTAIS E SALDOS
        # ====================================================

        if (
            linha_minuscula == "total"

            or

            linha_minuscula.startswith(
                "saldo anterior"
            )

            or

            linha_minuscula.startswith(
                "saldo em c/c"
            )

            or

            linha_minuscula.startswith(
                "saldo aplic aut mais"
            )
        ):

            historico_atual = None

            continue


        # ====================================================
        # DATA
        # ====================================================

        if (
            padrao_data_numerica.match(
                linha
            )

            or

            padrao_data_completa.match(
                linha
            )

            or

            padrao_data_mes_texto.match(
                linha
            )

            or

            padrao_data_mes_texto_espaco.match(
                linha
            )
        ):

            data_atual = formatar_data_extrato(
                linha,
                ano_extrato
            )


            historico_atual = None

            continue


        # ====================================================
        # VALOR
        # ====================================================

        if (
            padrao_valor.match(
                linha
            )

            and

            historico_atual
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
                    "Data":
                    data_atual,

                    "Histórico":
                    historico_atual,

                    "Débito":
                    debito,

                    "Crédito":
                    credito
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