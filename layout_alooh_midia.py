import os
import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ALOOH MIDIA - BRADESCO
# ============================================================

CONTA_BANCO = 11

CONTA_DEBITO_PADRAO = 1359

CONTA_CREDITO_PADRAO = 1360

CONTA_INVEST_FACIL = 32

MATRIZ_FILIAL = 2821


# ============================================================
# COLUNAS DE SAÍDA
# ============================================================

COLUNAS_SAIDA = [
    "Data",
    "CÓD CONTA DÉBITO",
    "CÓD CONTA CRÉDITO",
    "VALOR",
    "COD. HISTORICO",
    "COMPLEMENTO HISTÓRICO",
    "INICIAL LOTE",
    "MATRIZ/FILIAL",
    "CC DEBITO",
    "CC CRÉDITO"
]


# ============================================================
# NORMALIZA TEXTO PARA COMPARAÇÃO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# HISTÓRICO FINAL
# SEMPRE EM MAIÚSCULAS
# ============================================================

def formatar_historico(texto):

    if texto is None:
        return ""

    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


# ============================================================
# CONVERTE VALOR
# ============================================================

def para_decimal(valor):

    if valor is None:
        return Decimal("0")

    if pd.isna(valor):
        return Decimal("0")

    if isinstance(valor, Decimal):
        return valor

    if isinstance(valor, (int, float)):

        return Decimal(
            str(valor)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    texto = str(valor).strip()

    if not texto:
        return Decimal("0")

    texto = (
        texto
        .replace("R$", "")
        .replace(" ", "")
    )

    if "," in texto:

        texto = (
            texto
            .replace(".", "")
            .replace(",", ".")
        )

    try:

        return Decimal(
            texto
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    except InvalidOperation:

        return Decimal("0")


# ============================================================
# FORMATA VALOR
# ============================================================

def formatar_valor(valor):

    valor = para_decimal(
        valor
    )

    return (
        f"{valor:.2f}"
        .replace(".", ",")
    )


# ============================================================
# LEITURA DO ARQUIVO
# ============================================================

def ler_arquivo(caminho):

    extensao = os.path.splitext(
        caminho
    )[1].lower()

    if extensao in [
        ".xlsx",
        ".xls"
    ]:

        return pd.read_excel(
            caminho
        )

    if extensao == ".csv":

        tentativas = [
            {
                "sep": ";",
                "encoding": "utf-8-sig"
            },
            {
                "sep": ";",
                "encoding": "latin1"
            },
            {
                "sep": ",",
                "encoding": "utf-8-sig"
            },
            {
                "sep": ",",
                "encoding": "latin1"
            }
        ]

        ultimo_erro = None

        for config in tentativas:

            try:

                df = pd.read_csv(
                    caminho,
                    **config
                )

                if len(df.columns) >= 4:

                    return df

            except Exception as erro:

                ultimo_erro = erro

        raise ValueError(
            "Não foi possível ler o arquivo: "
            f"{ultimo_erro}"
        )

    raise ValueError(
        "Formato não suportado. "
        "Use CSV, XLS ou XLSX."
    )


# ============================================================
# LOCALIZA COLUNAS
# ============================================================

def localizar_colunas(df):

    mapa = {
        normalizar_texto(coluna):
        coluna
        for coluna in df.columns
    }

    def localizar(*nomes):

        for nome in nomes:

            chave = normalizar_texto(
                nome
            )

            if chave in mapa:

                return mapa[chave]

        return None


    col_data = localizar(
        "Data"
    )

    col_historico = localizar(
        "Histórico",
        "Historico",
        "Descrição",
        "Descricao"
    )

    col_credito = localizar(
        "Crédito",
        "Credito",
        "Entradas"
    )

    col_debito = localizar(
        "Débito",
        "Debito",
        "Saídas",
        "Saidas"
    )


    faltando = []

    if not col_data:
        faltando.append(
            "Data"
        )

    if not col_historico:
        faltando.append(
            "Histórico"
        )

    if not col_credito:
        faltando.append(
            "Crédito"
        )

    if not col_debito:
        faltando.append(
            "Débito"
        )


    if faltando:

        raise ValueError(
            "Colunas obrigatórias não encontradas: "
            + ", ".join(faltando)
        )


    return (
        col_data,
        col_historico,
        col_credito,
        col_debito
    )


# ============================================================
# CONVERTE DATA
# ============================================================

def converter_data(valor):

    if isinstance(
        valor,
        pd.Timestamp
    ):

        return valor

    data = pd.to_datetime(
        valor,
        dayfirst=True,
        errors="coerce"
    )

    if pd.isna(data):

        raise ValueError(
            f"Data inválida: {valor}"
        )

    return data


# ============================================================
# IDENTIFICA RENTABILIDADE INVEST FÁCIL
# ============================================================

def eh_rentabilidade_invest_facil(
    historico
):

    texto = normalizar_texto(
        historico
    )

    termos = [
        "RENTAB.INVEST FACIL",
        "RENTAB INVEST FACIL",
        "RENTABINVEST FACIL",
        "RENTAB.INVEST FACILCRED",
        "RENTAB INVEST FACILCRED",
        "RENTABINVEST FACILCRED"
    ]

    return any(
        termo in texto
        for termo in termos
    )


# ============================================================
# IDENTIFICA TED DEVOLVIDA
# ============================================================

def eh_ted_devolvida(
    historico
):

    texto = normalizar_texto(
        historico
    )

    termos = [
        "TED DEVOLVIDA",
        "DEVOLUCAO TED",
        "TED DEVOLUCAO"
    ]

    return any(
        termo in texto
        for termo in termos
    )


# ============================================================
# CLASSIFICA DÉBITO
# ============================================================

def classificar_debito(
    historico
):

    texto = normalizar_texto(
        historico
    )

    # ========================================================
    # REGRA PADRÃO CONFIRMADA NOS MESES ANALISADOS
    #
    # PIX ENVIADO
    # TED
    # BOLETOS
    # TRIBUTOS
    # CARTÃO
    # TARIFAS
    # DOC/TED INTERNET
    # DEMAIS PAGAMENTOS
    #
    # D 1359
    # C 11
    # ========================================================

    return CONTA_DEBITO_PADRAO


# ============================================================
# CLASSIFICA CRÉDITO
# ============================================================

def classificar_credito(
    historico
):

    # ========================================================
    # PRIORIDADE 1
    # RENTABILIDADE INVEST FÁCIL
    #
    # D 11
    # C 32
    # ========================================================

    if eh_rentabilidade_invest_facil(
        historico
    ):

        return CONTA_INVEST_FACIL


    # ========================================================
    # PRIORIDADE 2
    # TED DEVOLVIDA
    #
    # É ESTORNO / DEVOLUÇÃO DE PAGAMENTO
    #
    # D 11
    # C 1359
    # ========================================================

    if eh_ted_devolvida(
        historico
    ):

        return CONTA_DEBITO_PADRAO


    # ========================================================
    # PRIORIDADE 3
    # RECEBIMENTOS NORMAIS
    #
    # PIX RECEBIDO
    # TED RECEBIDA
    # TRANSFERÊNCIA RECEBIDA
    # DEMAIS ENTRADAS
    #
    # D 11
    # C 1360
    # ========================================================

    return CONTA_CREDITO_PADRAO


# ============================================================
# MONTA LINHA FINAL
# ============================================================

def nova_linha(
    data,
    conta_debito,
    conta_credito,
    valor,
    historico
):

    return {

        "Data":
        data.strftime(
            "%d/%m/%Y"
        ),

        "CÓD CONTA DÉBITO":
        conta_debito,

        "CÓD CONTA CRÉDITO":
        conta_credito,

        "VALOR":
        formatar_valor(
            valor
        ),

        "COD. HISTORICO":
        "",

        "COMPLEMENTO HISTÓRICO":
        formatar_historico(
            historico
        ),

        "INICIAL LOTE":
        "",

        "MATRIZ/FILIAL":
        MATRIZ_FILIAL,

        "CC DEBITO":
        "",

        "CC CRÉDITO":
        ""
    }


# ============================================================
# GERA LAYOUT FINAL
# ALOOH MIDIA
# ============================================================

def gerar_layout_alooh_midia(
    caminho_arquivo
):

    df = ler_arquivo(
        caminho_arquivo
    )


    (
        col_data,
        col_historico,
        col_credito,
        col_debito

    ) = localizar_colunas(
        df
    )


    # ========================================================
    # SEPARAÇÃO PARA CONFERÊNCIA
    #
    # PRIMEIRO DÉBITOS
    # DEPOIS CRÉDITOS
    # ========================================================

    registros_debito = []

    registros_credito = []


    # ========================================================
    # PROCESSA LANÇAMENTOS
    # ========================================================

    for _, linha in df.iterrows():

        data = converter_data(
            linha[col_data]
        )

        historico = str(
            linha[col_historico]
        ).strip()

        credito = para_decimal(
            linha[col_credito]
        )

        debito = para_decimal(
            linha[col_debito]
        )


        # ====================================================
        # DÉBITOS
        # ====================================================

        if debito > 0:

            conta_debito = (
                classificar_debito(
                    historico
                )
            )

            registro = nova_linha(
                data=data,
                conta_debito=conta_debito,
                conta_credito=CONTA_BANCO,
                valor=debito,
                historico=historico
            )

            registros_debito.append(
                {
                    "_data":
                    data,

                    "linha":
                    registro
                }
            )


        # ====================================================
        # CRÉDITOS
        # ====================================================

        if credito > 0:

            conta_credito = (
                classificar_credito(
                    historico
                )
            )

            registro = nova_linha(
                data=data,
                conta_debito=CONTA_BANCO,
                conta_credito=conta_credito,
                valor=credito,
                historico=historico
            )

            registros_credito.append(
                {
                    "_data":
                    data,

                    "linha":
                    registro
                }
            )


    # ========================================================
    # ORDENA CADA BLOCO POR DATA
    # ========================================================

    registros_debito.sort(
        key=lambda item:
        item["_data"]
    )

    registros_credito.sort(
        key=lambda item:
        item["_data"]
    )


    # ========================================================
    # JUNTA
    #
    # DÉBITOS PRIMEIRO
    # CRÉDITOS DEPOIS
    # ========================================================

    registros = (
        [
            item["linha"]
            for item
            in registros_debito
        ]
        +
        [
            item["linha"]
            for item
            in registros_credito
        ]
    )


    resultado = pd.DataFrame(
        registros,
        columns=COLUNAS_SAIDA
    )


    # ========================================================
    # DADOS PARA CONFERÊNCIA
    # ========================================================

    resultado.attrs[
        "quantidade_debitos"
    ] = len(
        registros_debito
    )

    resultado.attrs[
        "quantidade_creditos"
    ] = len(
        registros_credito
    )

    resultado.attrs[
        "quantidade_total"
    ] = len(
        registros
    )


    return resultado


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    import sys


    if len(sys.argv) < 2:

        print(
            "Uso:"
        )

        print(
            "python layout_alooh_midia.py arquivo.csv"
        )

        raise SystemExit(1)


    caminho = sys.argv[1]


    resultado = (
        gerar_layout_alooh_midia(
            caminho
        )
    )


    nome_base = os.path.splitext(
        os.path.basename(
            caminho
        )
    )[0]


    nome_saida = (
        f"{nome_base}"
        "_LAYOUT_ALOOH_MIDIA.csv"
    )


    caminho_saida = os.path.join(
        os.path.dirname(
            caminho
        ),
        nome_saida
    )


    resultado.to_csv(
        caminho_saida,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )


    print()

    print(
        "====================================="
    )

    print(
        "LAYOUT FINAL ALOOH MIDIA"
    )

    print(
        "====================================="
    )

    print(
        "Arquivo gerado:",
        caminho_saida
    )

    print()

    print(
        "Débitos:",
        resultado.attrs[
            "quantidade_debitos"
        ]
    )

    print(
        "Créditos:",
        resultado.attrs[
            "quantidade_creditos"
        ]
    )

    print(
        "Total:",
        resultado.attrs[
            "quantidade_total"
        ]
    )