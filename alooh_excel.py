import os
import re

import pandas as pd


# ============================================================
# CONVERTE VALOR BRASILEIRO
# ============================================================

def converter_valor_excel(valor):

    if valor is None:
        return None

    if pd.isna(valor):
        return None


    # ========================================================
    # SE JÁ FOR NÚMERO DO EXCEL
    # ========================================================

    if isinstance(valor, (int, float)):

        return float(valor)


    # ========================================================
    # CONVERTE PARA TEXTO
    # ========================================================

    texto = str(valor).strip()

    if texto == "":
        return None


    # ========================================================
    # REMOVE R$ E ESPAÇOS
    # ========================================================

    texto = (
        texto
        .replace("R$", "")
        .replace(" ", "")
    )


    # ========================================================
    # IDENTIFICA NEGATIVO
    # ========================================================

    negativo = False

    if texto.endswith("-"):

        negativo = True
        texto = texto[:-1]

    elif texto.startswith("-"):

        negativo = True
        texto = texto[1:]

    elif (
        texto.startswith("(")
        and texto.endswith(")")
    ):

        negativo = True
        texto = texto[1:-1]


    # ========================================================
    # PADRÃO BRASILEIRO
    #
    # 1.234,56
    # 1234,56
    # ========================================================

    if "," in texto:

        texto = (
            texto
            .replace(".", "")
            .replace(",", ".")
        )

    else:

        if texto.count(".") > 1:

            partes = texto.split(".")

            texto = (
                "".join(partes[:-1])
                + "."
                + partes[-1]
            )


    # ========================================================
    # REMOVE CARACTERES ESTRANHOS
    # ========================================================

    texto = re.sub(
        r"[^0-9.]",
        "",
        texto
    )


    if texto == "":
        return None


    try:

        numero = float(texto)

    except ValueError:

        return None


    if negativo:

        numero = -numero


    return numero


# ============================================================
# CONVERTE DATA
# ============================================================

def converter_data_excel(valor):

    if valor is None:
        return pd.NaT

    if pd.isna(valor):
        return pd.NaT


    # ========================================================
    # JÁ É DATA
    # ========================================================

    if isinstance(
        valor,
        pd.Timestamp
    ):

        return valor


    # ========================================================
    # TENTA CONVERTER NORMALMENTE
    # ========================================================

    try:

        resultado = pd.to_datetime(
            valor,
            errors="coerce",
            dayfirst=True
        )

        if not pd.isna(resultado):

            return resultado

    except Exception:

        pass


    # ========================================================
    # TENTA DATA SERIAL DO EXCEL
    # ========================================================

    try:

        numero = float(valor)

        if (
            numero > 20000
            and numero < 80000
        ):

            return pd.to_datetime(
                numero,
                unit="D",
                origin="1899-12-30"
            )

    except Exception:

        pass


    return pd.NaT


# ============================================================
# LEITOR ALOOH EXCEL
# ============================================================

def ler_alooh_excel(caminho_arquivo):

    # ========================================================
    # IDENTIFICA EXTENSÃO
    # ========================================================

    extensao = os.path.splitext(
        caminho_arquivo
    )[1].lower()


    # ========================================================
    # DEFINE ENGINE
    # ========================================================

    if extensao == ".xls":

        engine = "xlrd"

    elif extensao == ".xlsx":

        engine = "openpyxl"

    else:

        raise ValueError(
            f"Formato de arquivo não suportado: {extensao}"
        )


    print(
        "ALOOH - ARQUIVO:",
        caminho_arquivo
    )

    print(
        "ALOOH - EXTENSÃO:",
        extensao
    )

    print(
        "ALOOH - ENGINE:",
        engine
    )


    # ========================================================
    # LÊ O EXCEL BRUTO
    # ========================================================

    bruto = pd.read_excel(
        caminho_arquivo,
        header=None,
        engine=engine
    )


    print(
        "ALOOH - TOTAL DE LINHAS BRUTAS:",
        len(bruto)
    )


    # ========================================================
    # PROCURA CABEÇALHO DA MOVIMENTAÇÃO
    # ========================================================

    linha_cabecalho = None

    for i, linha in bruto.iterrows():

        valores = [
            str(valor)
            .strip()
            .upper()

            for valor
            in linha.tolist()
        ]

        texto = " ".join(
            valores
        )

        tem_data = (
            "DATA" in texto
        )

        tem_lancamento = (
            "LANÇAMENTO" in texto
            or
            "LANCAMENTO" in texto
        )

        tem_credito = (
            "CRÉDITO" in texto
            or
            "CREDITO" in texto
        )

        tem_debito = (
            "DÉBITO" in texto
            or
            "DEBITO" in texto
        )


        if (
            tem_data
            and tem_lancamento
            and tem_credito
            and tem_debito
        ):

            linha_cabecalho = i

            break


    if linha_cabecalho is None:

        raise ValueError(
            "Cabeçalho da movimentação não encontrado."
        )


    print(
        "ALOOH - CABEÇALHO:",
        linha_cabecalho
    )


    # ========================================================
    # PEGA A LINHA DO CABEÇALHO
    # ========================================================

    cabecalho = bruto.iloc[
        linha_cabecalho
    ]


    # ========================================================
    # LOCALIZA COLUNAS
    # ========================================================

    coluna_data = None
    coluna_historico = None
    coluna_credito = None
    coluna_debito = None


    for indice, valor in cabecalho.items():

        texto = (
            str(valor)
            .strip()
            .upper()
        )


        if texto == "DATA":

            coluna_data = indice


        elif (
            "LANÇAMENTO" in texto
            or
            "LANCAMENTO" in texto
        ):

            coluna_historico = indice


        elif (
            "CRÉDITO" in texto
            or
            "CREDITO" in texto
        ):

            coluna_credito = indice


        elif (
            "DÉBITO" in texto
            or
            "DEBITO" in texto
        ):

            coluna_debito = indice


    # ========================================================
    # VALIDA COLUNAS
    # ========================================================

    if coluna_data is None:

        raise ValueError(
            "Coluna DATA não encontrada."
        )

    if coluna_historico is None:

        raise ValueError(
            "Coluna LANÇAMENTO não encontrada."
        )

    if coluna_credito is None:

        raise ValueError(
            "Coluna CRÉDITO não encontrada."
        )

    if coluna_debito is None:

        raise ValueError(
            "Coluna DÉBITO não encontrada."
        )


    print(
        "ALOOH - COLUNA DATA:",
        coluna_data
    )

    print(
        "ALOOH - COLUNA HISTÓRICO:",
        coluna_historico
    )

    print(
        "ALOOH - COLUNA CRÉDITO:",
        coluna_credito
    )

    print(
        "ALOOH - COLUNA DÉBITO:",
        coluna_debito
    )


    # ========================================================
    # LOCALIZA O FIM DA MOVIMENTAÇÃO
    #
    # REGRA:
    # A PRIMEIRA LINHA "TOTAL" APÓS O CABEÇALHO
    # ENCERRA A MOVIMENTAÇÃO.
    # ========================================================

    linha_final = len(bruto)


    for i in range(
        linha_cabecalho + 1,
        len(bruto)
    ):

        linha = bruto.iloc[i]

        valores = [
            str(valor)
            .strip()
            .upper()

            for valor
            in linha.tolist()

            if not pd.isna(valor)
        ]


        # ----------------------------------------------------
        # VERIFICA SE ALGUMA CÉLULA É EXATAMENTE "TOTAL"
        # ----------------------------------------------------

        encontrou_total = any(
            valor == "TOTAL"
            for valor in valores
        )


        if encontrou_total:

            linha_final = i

            print(
                "ALOOH - TOTAL ENCONTRADO NA LINHA:",
                i
            )

            break


    # ========================================================
    # PEGA SOMENTE A MOVIMENTAÇÃO
    #
    # CABEÇALHO
    # ↓
    # MOVIMENTOS
    # ↓
    # TOTAL
    #
    # NÃO PEGA NADA DEPOIS DO TOTAL.
    # ========================================================

    df = bruto.iloc[
        linha_cabecalho + 1:
        linha_final
    ].copy()


    print(
        "ALOOH - LINHAS DA MOVIMENTAÇÃO:",
        len(df)
    )


    # ========================================================
    # SELECIONA COLUNAS
    # ========================================================

    df = df[
        [
            coluna_data,
            coluna_historico,
            coluna_credito,
            coluna_debito
        ]
    ].copy()


    df.columns = [
        "Data",
        "Histórico",
        "Crédito",
        "Débito"
    ]


    # ========================================================
    # LIMPA HISTÓRICO
    # ========================================================

    df["Histórico"] = (
        df["Histórico"]
        .fillna("")
        .astype(str)
        .str.strip()
    )


    # ========================================================
    # REMOVE SALDO ANTERIOR
    # ========================================================

    df = df[
        ~df["Histórico"]
        .str.upper()
        .str.contains(
            "SALDO ANTERIOR",
            na=False
        )
    ].copy()


    # ========================================================
    # CONVERTE DATA
    # ========================================================

    df["Data"] = (
        df["Data"]
        .apply(
            converter_data_excel
        )
    )


    # ========================================================
    # CONVERTE CRÉDITO
    # ========================================================

    df["Crédito"] = (
        df["Crédito"]
        .apply(
            converter_valor_excel
        )
    )


    # ========================================================
    # CONVERTE DÉBITO
    # ========================================================

    df["Débito"] = (
        df["Débito"]
        .apply(
            converter_valor_excel
        )
    )


    # ========================================================
    # DÉBITO POSITIVO
    # ========================================================

    df["Débito"] = (
        df["Débito"]
        .apply(
            lambda valor:
            abs(valor)
            if valor is not None
            and not pd.isna(valor)
            else None
        )
    )


    # ========================================================
    # SOMENTE DATA VÁLIDA
    # ========================================================

    df = df[
        df["Data"].notna()
    ].copy()


    # ========================================================
    # SOMENTE LINHAS COM MOVIMENTO
    # ========================================================

    df = df[
        df["Crédito"].notna()
        |
        df["Débito"].notna()
    ].copy()


    # ========================================================
    # FORMATA DATA
    # ========================================================

    df["Data"] = (
        df["Data"]
        .dt.strftime(
            "%d/%m/%Y"
        )
    )


    # ========================================================
    # ORGANIZA ÍNDICE
    # ========================================================

    df = df.reset_index(
        drop=True
    )


    print(
        "ALOOH - LANÇAMENTOS FINAIS:",
        len(df)
    )


    # ========================================================
    # RETORNA
    # ========================================================

    return df