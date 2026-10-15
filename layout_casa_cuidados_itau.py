import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# CASA DE CUIDADOS - ITAÚ
# ============================================================

CONTA_BANCO = 11

CONTA_DEBITO_PADRAO = 1724

CONTA_CREDITO_PADRAO = 1725

CONTA_APLICACAO = 1519

MATRIZ_FILIAL = 276


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
# NORMALIZA TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    if pd.isna(texto):
        return ""

    return (
        str(texto)
        .strip()
        .upper()
    )


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

    texto = (
        f"{valor:.2f}"
        .replace(".", ",")
    )

    if texto.endswith(",00"):
        return texto[:-3]

    if texto.endswith("0"):
        return texto[:-1]

    return texto


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
# LOCALIZA AS COLUNAS
# ============================================================

def localizar_colunas(df):

    mapa = {
        normalizar_texto(coluna):
        coluna

        for coluna
        in df.columns
    }


    def localizar(*nomes):

        for nome in nomes:

            nome_normalizado = (
                normalizar_texto(
                    nome
                )
            )

            if nome_normalizado in mapa:

                return mapa[
                    nome_normalizado
                ]

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


    col_debito = localizar(
        "Débito",
        "Debito",
        "Saídas",
        "Saidas"
    )


    col_credito = localizar(
        "Crédito",
        "Credito",
        "Entradas"
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


    if not col_debito:
        faltando.append(
            "Débito"
        )


    if not col_credito:
        faltando.append(
            "Crédito"
        )


    if faltando:

        raise ValueError(
            "Colunas obrigatórias não encontradas: "
            +
            ", ".join(
                faltando
            )
        )


    return (
        col_data,
        col_historico,
        col_debito,
        col_credito
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
# MONTA LINHA
# ============================================================

def nova_linha(
    data,
    debito,
    credito,
    valor,
    historico
):

    return {

        "Data":
        data.strftime(
            "%d/%m/%Y"
        ),

        "CÓD CONTA DÉBITO":
        debito,

        "CÓD CONTA CRÉDITO":
        credito,

        "VALOR":
        formatar_valor(
            valor
        ),

        "COD. HISTORICO":
        "",

        "COMPLEMENTO HISTÓRICO":
        str(historico).strip().upper(),

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
# IDENTIFICA APLICAÇÃO AUT MAIS
# ============================================================

def eh_aplicacao_aut_mais(
    historico
):

    texto = normalizar_texto(
        historico
    )


    return (
        "APL APLIC AUT MAIS"
        in texto

        or

        "APLIC AUT MAIS"
        in texto

        or

        "APLICAÇÃO AUT MAIS"
        in texto

        or

        "APLICACAO AUT MAIS"
        in texto
    ) and not (
        "RES APLIC AUT MAIS"
        in texto

        or

        "RESGATE"
        in texto

        or

        "REND PAGO"
        in texto
    )


# ============================================================
# IDENTIFICA RESGATE AUT MAIS
# ============================================================

def eh_resgate_aut_mais(
    historico
):

    texto = normalizar_texto(
        historico
    )


    return (
        "RES APLIC AUT MAIS"
        in texto

        or

        "RESGATE AUT MAIS"
        in texto

        or

        "RESGATE DE APLICACAO"
        in texto

        or

        "RESGATE DE APLICAÇÃO"
        in texto
    )


# ============================================================
# IDENTIFICA RENDIMENTO AUT MAIS
# ============================================================

def eh_rendimento_aut_mais(
    historico
):

    texto = normalizar_texto(
        historico
    )


    return (
        "REND PAGO APLIC AUT MAIS"
        in texto

        or

        "RENDIMENTO"
        in texto
    )


# ============================================================
# GERA LAYOUT
# ============================================================

def gerar_layout_casa_cuidados_itau(
    caminho_arquivo
):

    df = ler_arquivo(
        caminho_arquivo
    )


    (
        col_data,
        col_historico,
        col_debito,
        col_credito

    ) = localizar_colunas(
        df
    )


    # ========================================================
    # SEPARAÇÃO PARA FACILITAR CONFERÊNCIA
    #
    # PRIMEIRO:
    # TODOS OS DÉBITOS
    #
    # DEPOIS:
    # TODOS OS CRÉDITOS
    # ========================================================

    registros_debito = []

    registros_credito = []


    # ========================================================
    # PROCESSA LINHAS
    # ========================================================

    for _, linha in df.iterrows():

        data = converter_data(
            linha[col_data]
        )


        historico = str(
            linha[col_historico]
        ).strip()


        debito = para_decimal(
            linha[col_debito]
        )


        credito = para_decimal(
            linha[col_credito]
        )


        # ====================================================
        # DÉBITOS
        # ====================================================

        if debito > 0:

            # ================================================
            # APLICAÇÃO AUT MAIS
            #
            # D 1519
            # C 11
            # ================================================

            if eh_aplicacao_aut_mais(
                historico
            ):

                conta_debito = (
                    CONTA_APLICACAO
                )


            # ================================================
            # DÉBITO NORMAL
            #
            # D 1724
            # C 11
            # ================================================

            else:

                conta_debito = (
                    CONTA_DEBITO_PADRAO
                )


            registros_debito.append(
                {
                    "_data_ordenacao":
                    data,

                    "linha":
                    nova_linha(
                        data=data,
                        debito=conta_debito,
                        credito=CONTA_BANCO,
                        valor=debito,
                        historico=historico
                    )
                }
            )


        # ====================================================
        # CRÉDITOS
        # ====================================================

        if credito > 0:

            # ================================================
            # CRÉDITO NORMAL
            #
            # D 11
            # C 1725
            # ================================================
            #
            # RESGATE AUT MAIS TAMBÉM SEGUE:
            #
            # D 11
            # C 1725
            #
            # RENDIMENTO AUT MAIS TAMBÉM SEGUE:
            #
            # D 11
            # C 1725
            # ================================================

            conta_credito = (
                CONTA_CREDITO_PADRAO
            )


            registros_credito.append(
                {
                    "_data_ordenacao":
                    data,

                    "linha":
                    nova_linha(
                        data=data,
                        debito=CONTA_BANCO,
                        credito=conta_credito,
                        valor=credito,
                        historico=historico
                    )
                }
            )


    # ========================================================
    # ORDENA CADA BLOCO POR DATA
    #
    # IMPORTANTE:
    #
    # NÃO MISTURA DÉBITO COM CRÉDITO.
    #
    # FICA:
    #
    # DÉBITOS
    # ↓
    # CRÉDITOS
    # ========================================================

    registros_debito.sort(
        key=lambda item:
        item["_data_ordenacao"]
    )


    registros_credito.sort(
        key=lambda item:
        item["_data_ordenacao"]
    )


    # ========================================================
    # JUNTA OS BLOCOS
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


    # ========================================================
    # RESULTADO
    # ========================================================

    return pd.DataFrame(
        registros,
        columns=COLUNAS_SAIDA
    )


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
            "python layout_casa_cuidados_itau.py arquivo.csv"
        )

        raise SystemExit(1)


    caminho = sys.argv[1]


    resultado = (
        gerar_layout_casa_cuidados_itau(
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
        "_LAYOUT_CASA_CUIDADOS_ITAU.csv"
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


    print(
        "Arquivo gerado:"
    )

    print(
        caminho_saida
    )


    print()


    print(
        "Quantidade de lançamentos:"
    )

    print(
        len(resultado)
    )