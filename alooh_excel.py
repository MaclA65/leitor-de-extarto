import pandas as pd


def ler_alooh_excel(caminho_arquivo):

    bruto = pd.read_excel(
        caminho_arquivo,
        header=None,
        engine="xlrd"
    )

    # =====================================
    # PROCURA O CABEÇALHO REAL
    # =====================================

    linha_cabecalho = None

    for i, linha in bruto.iterrows():

        valores = [
            str(valor).upper()
            for valor in linha.tolist()
        ]

        texto = " ".join(valores)

        if (
            "DATA" in texto
            and "LANÇAMENTO" in texto
            and "CRÉDITO" in texto
            and "DÉBITO" in texto
        ):
            linha_cabecalho = i
            break

    if linha_cabecalho is None:
        raise ValueError(
            "Cabeçalho da movimentação não encontrado."
        )

    # =====================================
    # PEGA SOMENTE DEPOIS DO CABEÇALHO
    # =====================================

    df = bruto.iloc[
        linha_cabecalho + 1:
    ].copy()

    # =====================================
    # MANTÉM SOMENTE:
    # Data / Lançamento / Crédito / Débito
    # =====================================

    df = df.iloc[:, [0, 1, 3, 4]]

    df.columns = [
        "Data",
        "Histórico",
        "Crédito",
        "Débito"
    ]

    # =====================================
    # CONVERTE DATA
    # =====================================

    df["Data"] = pd.to_datetime(
        df["Data"],
        errors="coerce",
        dayfirst=True
    )

    # Só mantém linhas com data válida
    df = df[
        df["Data"].notna()
    ].copy()

    df["Data"] = (
        df["Data"]
        .dt.strftime("%d/%m/%Y")
    )

    # =====================================
    # REMOVE SALDO ANTERIOR
    # =====================================

    df = df[
        ~df["Histórico"]
        .astype(str)
        .str.upper()
        .str.contains(
            "SALDO ANTERIOR",
            na=False
        )
    ]

    # =====================================
    # CONVERTE VALORES
    # =====================================

    df["Crédito"] = pd.to_numeric(
        df["Crédito"],
        errors="coerce"
    )

    df["Débito"] = pd.to_numeric(
        df["Débito"],
        errors="coerce"
    )

    # Débito positivo
    df["Débito"] = df["Débito"].abs()

    # =====================================
    # SÓ MANTÉM LINHAS COM MOVIMENTO
    # =====================================

    df = df[
        df["Crédito"].notna()
        |
        df["Débito"].notna()
    ].copy()

    # =====================================
    # ORGANIZA ÍNDICE
    # =====================================

    df = df.reset_index(drop=True)

    return df