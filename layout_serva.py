import os
import re
import unicodedata

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd


# ============================================================
# CONTAS SERVA
# ============================================================

CONTA_BANCO = 10

MATRIZ_FILIAL = 2843

CONTA_APLICACAO = 32

CONTA_DESPESA_BANCARIA = 687

CONTA_PRO_LABORE = 244

CONTA_EDSON = 1246

CONTA_VERA = 1247

CONTA_ALUGUEL = 1217

CONTA_ENEL = 598

CONTA_CLARO = 600

CONTA_INSS = 252

CONTA_SIMPLES = 1216

CONTA_DEBITO_PADRAO = 1250

CONTA_CREDITO_PADRAO = 1251


VALOR_PRO_LABORE = Decimal(
    "1442.69"
)


# ============================================================
# COLUNAS DO LAYOUT FINAL
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
# SÓCIOS
# ============================================================

SOCIOS = {

    "edson": {

        "padroes": [
            "EDSON PEDRO"
        ],

        "conta":
        CONTA_EDSON,

        "nome":
        "EDSON PEDRO MARQUES"

    },


    "vera": {

        "padroes": [
            "VERA LUCIA B",
            "VERA LUCIA BRAGA"
        ],

        "conta":
        CONTA_VERA,

        "nome":
        "VERA LUCIA BRAGA RODRIGUES DE MORAES GALANTE"

    }

}


# ============================================================
# FORNECEDORES QUE VÃO PARA CONTA DO EDSON
# ============================================================

FORNECEDORES_EDSON = [

    (
        "RENATA DO REGO",
        "RENATA DO REGO ESTRELLA"
    ),

    (
        "JOAO PAULO D",
        "JOAO PAULO DO NASCIMENTO"
    ),

    (
        "MIRIAM TEREZ",
        "MIRIAM TEREZINHA DA FONSECA"
    ),

    (
        "CICERO DA SI",
        "CICERO DA SILVA BERNARDO"
    ),

    (
        "LUIZ HENRIQU",
        "LUIZ HENRIQUE GOMES DA SILVA"
    ),

    (
        "MARCOS ANTON",
        "MARCOS ANTONIO LINS DA SILVA"
    )

]


# ============================================================
# NORMALIZA TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:

        return ""


    if (
        isinstance(
            texto,
            float
        )
        and
        pd.isna(
            texto
        )
    ):

        return ""


    texto = str(
        texto
    ).upper().strip()


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


    texto = re.sub(
        r"\s+",
        " ",
        texto
    )


    return texto


# ============================================================
# CONVERTE VALOR PARA DECIMAL
# ============================================================

def para_decimal(valor):

    if valor is None:

        return Decimal(
            "0"
        )


    if (
        isinstance(
            valor,
            float
        )
        and
        pd.isna(
            valor
        )
    ):

        return Decimal(
            "0"
        )


    if isinstance(
        valor,
        Decimal
    ):

        return valor


    if isinstance(
        valor,
        (
            int,
            float
        )
    ):

        return Decimal(
            str(
                valor
            )
        ).quantize(

            Decimal(
                "0.01"
            ),

            rounding=
            ROUND_HALF_UP

        )


    texto = str(
        valor
    ).strip()


    texto = (
        texto
        .replace(
            "R$",
            ""
        )
        .replace(
            " ",
            ""
        )
    )


    if not texto:

        return Decimal(
            "0"
        )


    if "," in texto:

        texto = (
            texto
            .replace(
                ".",
                ""
            )
            .replace(
                ",",
                "."
            )
        )


    try:

        return Decimal(
            texto
        ).quantize(

            Decimal(
                "0.01"
            ),

            rounding=
            ROUND_HALF_UP

        )


    except InvalidOperation:

        return Decimal(
            "0"
        )


# ============================================================
# FORMATA VALOR
# ============================================================

def formatar_valor(valor):

    valor = para_decimal(
        valor
    )


    valor = valor.quantize(

        Decimal(
            "0.01"
        ),

        rounding=
        ROUND_HALF_UP

    )


    texto = (
        f"{valor:.2f}"
        .replace(
            ".",
            ","
        )
    )


    if texto.endswith(
        ",00"
    ):

        return texto[:-3]


    if texto.endswith(
        "0"
    ):

        return texto[:-1]


    return texto


# ============================================================
# LEITURA DO ARQUIVO
# ============================================================

def ler_arquivo(caminho):

    extensao = os.path.splitext(
        caminho
    )[1].lower()


    # ========================================================
    # EXCEL
    # ========================================================

    if extensao in [
        ".xlsx",
        ".xls"
    ]:

        return pd.read_excel(
            caminho
        )


    # ========================================================
    # CSV
    # ========================================================

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


                if len(
                    df.columns
                ) >= 4:

                    return df


            except Exception as erro:

                ultimo_erro = erro


        raise ValueError(

            "Não foi possível ler o CSV: "
            f"{ultimo_erro}"

        )


    raise ValueError(

        "Formato não suportado. "
        "Use CSV, XLS ou XLSX."

    )


# ============================================================
# LOCALIZA AS COLUNAS DO EXTRATO LIDO
# ============================================================

def localizar_colunas(df):

    mapa = {

        normalizar_texto(
            coluna
        ):
        coluna

        for coluna
        in df.columns

    }


    def procurar(
        *nomes
    ):

        for nome in nomes:

            nome_normalizado = normalizar_texto(
                nome
            )


            if nome_normalizado in mapa:

                return mapa[
                    nome_normalizado
                ]


        return None


    col_data = procurar(
        "Data"
    )


    col_historico = procurar(
        "Histórico",
        "Historico"
    )


    col_debito = procurar(
        "Débito",
        "Debito"
    )


    col_credito = procurar(
        "Crédito",
        "Credito"
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

        return valor.to_pydatetime()


    if isinstance(
        valor,
        datetime
    ):

        return valor


    if (
        isinstance(
            valor,
            (
                int,
                float
            )
        )
        and
        not pd.isna(
            valor
        )
    ):

        try:

            data = pd.to_datetime(

                valor,

                unit="D",

                origin=
                "1899-12-30"

            )


            return data.to_pydatetime()


        except Exception:

            pass


    texto = str(
        valor
    ).strip()


    formatos = [

        "%d/%m/%Y",

        "%Y-%m-%d",

        "%d/%m/%y"

    ]


    for formato in formatos:

        try:

            return datetime.strptime(
                texto,
                formato
            )

        except ValueError:

            continue


    data = pd.to_datetime(

        texto,

        dayfirst=True,

        errors="coerce"

    )


    if pd.isna(
        data
    ):

        raise ValueError(

            f"Data inválida: {valor}"

        )


    return data.to_pydatetime()


# ============================================================
# COMPETÊNCIA ANTERIOR
# ALUGUEL / ENEL
# ============================================================

def competencia_anterior(data):

    ano = data.year

    mes = (
        data.month
        - 1
    )


    if mes == 0:

        mes = 12

        ano -= 1


    return (
        f"{mes:02d}/{ano}"
    )


# ============================================================
# MONTA UMA LINHA DO LAYOUT
# ============================================================

def nova_linha(

    data,

    debito="",

    credito="",

    valor=
    Decimal(
        "0"
    ),

    historico="",

    inicial_lote="",

    matriz=
    MATRIZ_FILIAL

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
        historico,

        "INICIAL LOTE":
        inicial_lote,

        "MATRIZ/FILIAL":
        matriz,

        "CC DEBITO":
        "",

        "CC CRÉDITO":
        ""

    }


# ============================================================
# IDENTIFICA SÓCIO
# ============================================================

def identificar_socio(
    historico
):

    historico_normalizado = (
        normalizar_texto(
            historico
        )
    )


    for chave, info in SOCIOS.items():

        for padrao in info[
            "padroes"
        ]:

            if padrao in historico_normalizado:

                return chave


    return None


# ============================================================
# LOCALIZA O PAGAMENTO DE PRÓ-LABORE
# ============================================================

def selecionar_pro_labore(

    df,

    col_data,

    col_historico,

    col_debito

):

    selecionados = set()

    grupos = {}


    for indice, linha in df.iterrows():

        valor = para_decimal(
            linha[
                col_debito
            ]
        )


        if valor <= 0:

            continue


        socio = identificar_socio(

            linha[
                col_historico
            ]

        )


        if not socio:

            continue


        data = converter_data(

            linha[
                col_data
            ]

        )


        # ====================================================
        # SOMENTE PAGAMENTOS ATÉ O DIA 10
        # ====================================================

        if data.day > 10:

            continue


        chave = (

            socio,

            data.year,

            data.month

        )


        if chave not in grupos:

            grupos[
                chave
            ] = []


        grupos[
            chave
        ].append(

            (
                indice,
                valor
            )

        )


    # ========================================================
    # PEGA O MAIOR PAGAMENTO ATÉ O DIA 10
    # ========================================================

    for itens in grupos.values():

        indice, maior_valor = max(

            itens,

            key=
            lambda item:
            item[1]

        )


        # ====================================================
        # SÓ DIVIDE SE O PAGAMENTO FOR >= 1.442,69
        # ====================================================

        if maior_valor >= VALOR_PRO_LABORE:

            selecionados.add(
                indice
            )


    return selecionados


# ============================================================
# IDENTIFICA FORNECEDORES ESPECIAIS
# ============================================================

def classificar_fornecedor_especial(
    historico
):

    historico_normalizado = (
        normalizar_texto(
            historico
        )
    )


    for (
        padrao,
        nome_completo

    ) in FORNECEDORES_EDSON:


        if padrao in historico_normalizado:

            return nome_completo


    return None


# ============================================================
# CLASSIFICA DÉBITO
# ============================================================

def classificar_debito(

    data,

    historico,

    valor,

    tributos=None

):

    historico_normalizado = (
        normalizar_texto(
            historico
        )
    )


    # ========================================================
    # FORNECEDORES ESPECIAIS → 1246
    # ========================================================

    fornecedor = (
        classificar_fornecedor_especial(
            historico
        )
    )


    if fornecedor:

        return (

            CONTA_EDSON,

            (
                "DEBITO - ITAU - PAGTO A "
                f"{fornecedor} "
                "CFE EXTRATO"
            )

        )


    # ========================================================
    # SÓCIOS
    # ========================================================

    socio = identificar_socio(
        historico
    )


    if socio:

        info = SOCIOS[
            socio
        ]


        return (

            info[
                "conta"
            ],

            (
                "DEBITO - ITAU - PAGTO. A "
                f"{info['nome']} "
                "CFE. EXTRATO"
            )

        )


    # ========================================================
    # ANTONIO DA CUNHA
    # ========================================================

    if (
        "ANTONIO DA C"
        in historico_normalizado

        or

        "ANTONIO DA CUNHA"
        in historico_normalizado
    ):

        competencia = (
            competencia_anterior(
                data
            )
        )


        return (

            CONTA_ALUGUEL,

            (
                "DEBITO - ITAU - PAGTO. "
                "A ANTONIO DA CUNHA "
                "REF. ALUGUEL "
                f"{competencia} "
                "CFE EXTRATO"
            )

        )


    # ========================================================
    # ENEL / ELETROPAULO
    # ========================================================

    if (
        "ELETROPAULO"
        in historico_normalizado

        or

        "ENEL"
        in historico_normalizado
    ):

        competencia = (
            competencia_anterior(
                data
            )
        )


        return (

            CONTA_ENEL,

            (
                "DEBITO - ITAU - PAGTO. "
                "A ENEL REF. "
                f"{competencia} "
                "CFE. EXTRATO"
            )

        )


    # ========================================================
    # CLARO
    # ========================================================

    if "CLARO" in historico_normalizado:

        return (

            CONTA_CLARO,

            (
                "DEBITO - ITAU - "
                "PAGTO A CLARO "
                "CFE EXTRATO"
            )

        )


    # ========================================================
    # APLICAÇÃO AUT MAIS
    # ========================================================

    if (
        "APLIC"
        in historico_normalizado

        and

        "AUT MAIS"
        in historico_normalizado
    ):

        return (

            CONTA_APLICACAO,

            (
                "APLICACAO FINANCEIRA "
                "AUT MAIS CFE EXTRATO"
            )

        )


    # ========================================================
    # IOF
    # ========================================================

    if "IOF" in historico_normalizado:

        # ====================================================
        # IOF DE APLICAÇÃO
        # ====================================================

        if (
            "APLIC"
            in historico_normalizado

            or

            "AUT MAIS"
            in historico_normalizado

            or

            "REND"
            in historico_normalizado
        ):

            return (

                CONTA_DESPESA_BANCARIA,

                (
                    "IOF S/RENDIMENTO DE "
                    "APLICACAO FINANCEIRA "
                    "BANCO ITAU AUT MAIS"
                )

            )


        # ====================================================
        # IOF CONTA CORRENTE
        # ====================================================

        return (

            CONTA_DESPESA_BANCARIA,

            (
                "DEBITO DE DESPESA "
                "COM IOF CFE EXTRATO"
            )

        )


    # ========================================================
    # TARIFAS / COMISSÕES
    # ========================================================

    if (
        historico_normalizado.startswith(
            "TAR"
        )

        or

        "TARIFA"
        in historico_normalizado

        or

        "COMISSAO"
        in historico_normalizado
    ):

        return (

            CONTA_DESPESA_BANCARIA,

            (
                "DEBITO DE DESPESA "
                "BANCARIA CFE EXTRATO"
            )

        )


    # ========================================================
    # TRIBUTOS
    #
    # NÃO CLASSIFICA SEM A GUIA
    # ========================================================

    if (
        "TRIB"
        in historico_normalizado

        or

        "DARF"
        in historico_normalizado

        or

        "GPS"
        in historico_normalizado

        or

        "INSS"
        in historico_normalizado

        or

        "SIMPLES"
        in historico_normalizado
    ):

        regra = None


        if tributos:

            regra = tributos.get(
                valor
            )


            if regra is None:

                regra = tributos.get(
                    str(
                        valor
                    )
                )


        if regra:

            tipo = normalizar_texto(

                regra.get(
                    "tipo",
                    ""
                )

            )


            competencia = regra.get(

                "competencia",
                ""

            )


            # ================================================
            # INSS
            # ================================================

            if tipo == "INSS":

                return (

                    CONTA_INSS,

                    (
                        "DEBITO - ITAU -  "
                        "RECOLHIMENTO INSS "
                        "S/ FOLHA REF. MES "
                        f"{competencia} "
                        "CFE DARF"
                    )

                )


            # ================================================
            # SIMPLES NACIONAL
            # ================================================

            if tipo in [

                "SIMPLES",

                "SIMPLES NACIONAL"

            ]:

                return (

                    CONTA_SIMPLES,

                    (
                        "DEBITO - ITAU -  "
                        "RECOLHIMENTO "
                        "SIMPLES NACIONAL "
                        "REF. MES "
                        f"{competencia} "
                        "CFE DARF"
                    )

                )


    # ========================================================
    # DÉBITO PADRÃO
    # ========================================================

    return (

        CONTA_DEBITO_PADRAO,

        str(
            historico
        ).strip()

    )


# ============================================================
# CLASSIFICA CRÉDITO
# ============================================================

def classificar_credito(
    historico
):

    historico_normalizado = (
        normalizar_texto(
            historico
        )
    )


    # ========================================================
    # RESGATE AUT MAIS
    # ========================================================

    if (

        "RES APLIC AUT MAIS"
        in historico_normalizado

        or

        (
            "RESGATE"
            in historico_normalizado

            and

            "AUT MAIS"
            in historico_normalizado
        )

    ):

        return (

            CONTA_APLICACAO,

            (
                "RESGATE DE APLICACAO "
                "FINANCEIRA AUT MAIS "
                "CFE EXTRATO"
            )

        )


    # ========================================================
    # DEMAIS CRÉDITOS
    # ========================================================

    return (

        CONTA_CREDITO_PADRAO,

        str(
            historico
        ).strip()

    )


# ============================================================
# GERA LAYOUT SERVA
# ============================================================

def gerar_layout_serva(

    caminho_arquivo,

    tributos=None

):

    # ========================================================
    # LÊ ARQUIVO CONFERIDO
    # ========================================================

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
    # LOCALIZA PRÓ-LABORE
    # ========================================================

    pro_labore_indices = (
        selecionar_pro_labore(

            df,

            col_data,

            col_historico,

            col_debito

        )
    )


    linhas_pro_labore = []

    linhas_debito = []

    linhas_credito = []

    avisos = []


    # ========================================================
    # PROCESSA TODAS AS LINHAS
    # ========================================================

    for indice, linha in df.iterrows():

        data = converter_data(

            linha[
                col_data
            ]

        )


        if pd.isna(

            linha[
                col_historico
            ]

        ):

            historico = ""

        else:

            historico = str(

                linha[
                    col_historico
                ]

            ).strip()


        debito = para_decimal(

            linha[
                col_debito
            ]

        )


        credito = para_decimal(

            linha[
                col_credito
            ]

        )


        # ====================================================
        # DÉBITOS
        # ====================================================

        if debito > 0:

            socio = identificar_socio(
                historico
            )


            # =================================================
            # PRÓ-LABORE
            # =================================================

            if (
                indice
                in
                pro_labore_indices

                and

                socio
            ):

                info = SOCIOS[
                    socio
                ]


                residual = (

                    debito
                    -
                    VALOR_PRO_LABORE

                ).quantize(

                    Decimal(
                        "0.01"
                    )

                )


                historico_socio = (

                    "DEBITO - ITAU - "
                    "PAGTO. A "
                    f"{info['nome']} "
                    "CFE. EXTRATO"

                )


                historico_pro_labore = (

                    "DEBITO - ITAU - "
                    "PAGTO. A "
                    f"{info['nome']} "
                    "REF. PRO-LABORE "
                    "CFE. EXTRATO"

                )


                # =============================================
                # LINHA DE CRÉDITO DO BANCO
                # VALOR INTEGRAL
                # =============================================

                linhas_pro_labore.append(

                    nova_linha(

                        data,

                        debito="",

                        credito=
                        CONTA_BANCO,

                        valor=
                        debito,

                        historico=
                        historico_socio,

                        inicial_lote=
                        1,

                        matriz=
                        MATRIZ_FILIAL

                    )

                )


                # =============================================
                # RESIDUAL PARA CONTA DO SÓCIO
                # =============================================

                if residual > 0:

                    linhas_pro_labore.append(

                        nova_linha(

                            data,

                            debito=
                            info[
                                "conta"
                            ],

                            credito="",

                            valor=
                            residual,

                            historico=
                            historico_socio,

                            inicial_lote="",

                            matriz=""

                        )

                    )


                # =============================================
                # PRÓ-LABORE → 244
                # =============================================

                linhas_pro_labore.append(

                    nova_linha(

                        data,

                        debito=
                        CONTA_PRO_LABORE,

                        credito="",

                        valor=
                        VALOR_PRO_LABORE,

                        historico=
                        historico_pro_labore,

                        inicial_lote="",

                        matriz=""

                    )

                )


                continue


            # =================================================
            # DEMAIS DÉBITOS
            # =================================================

            (
                conta_debito,
                historico_saida

            ) = classificar_debito(

                data,

                historico,

                debito,

                tributos=
                tributos

            )


            # =================================================
            # AVISO PARA TRIBUTO SEM GUIA
            # =================================================

            historico_normalizado = (
                normalizar_texto(
                    historico
                )
            )


            if (

                (
                    "TRIB"
                    in
                    historico_normalizado

                    or

                    "DARF"
                    in
                    historico_normalizado

                    or

                    "GPS"
                    in
                    historico_normalizado

                    or

                    "INSS"
                    in
                    historico_normalizado

                    or

                    "SIMPLES"
                    in
                    historico_normalizado
                )

                and

                conta_debito
                ==
                CONTA_DEBITO_PADRAO

            ):

                avisos.append(

                    (
                        data.strftime(
                            "%d/%m/%Y"
                        )
                        +
                        " | "
                        +
                        formatar_valor(
                            debito
                        )
                        +
                        " | "
                        +
                        historico
                        +
                        " | "
                        +
                        "TRIBUTO NÃO IDENTIFICADO: "
                        "conferir guia/comprovante."
                    )

                )


            linhas_debito.append(

                nova_linha(

                    data,

                    debito=
                    conta_debito,

                    credito=
                    CONTA_BANCO,

                    valor=
                    debito,

                    historico=
                    historico_saida

                )

            )


        # ====================================================
        # CRÉDITOS
        # ====================================================

        if credito > 0:

            (
                conta_credito,
                historico_saida

            ) = classificar_credito(
                historico
            )


            linhas_credito.append(

                nova_linha(

                    data,

                    debito=
                    CONTA_BANCO,

                    credito=
                    conta_credito,

                    valor=
                    credito,

                    historico=
                    historico_saida

                )

            )


    # ========================================================
    # ORDEM FINAL
    #
    # 1 - COMPOSIÇÕES DE PRÓ-LABORE
    # 2 - DÉBITOS
    # 3 - CRÉDITOS
    # ========================================================

    resultado = pd.DataFrame(

        (
            linhas_pro_labore
            +
            linhas_debito
            +
            linhas_credito
        ),

        columns=
        COLUNAS_SAIDA

    )


    resultado.attrs[
        "avisos"
    ] = avisos


    return resultado


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    import sys


    if len(
        sys.argv
    ) < 2:

        print(

            "Uso: "
            "python layout_serva.py "
            "arquivo.csv"

        )

        raise SystemExit(
            1
        )


    caminho = sys.argv[
        1
    ]


    df_saida = (
        gerar_layout_serva(
            caminho
        )
    )


    nome_base = os.path.splitext(

        os.path.basename(
            caminho
        )

    )[0]


    caminho_saida = os.path.join(

        os.path.dirname(
            caminho
        ),

        (
            f"{nome_base}"
            "_LAYOUT_SERVA.csv"
        )

    )


    df_saida.to_csv(

        caminho_saida,

        sep=";",

        index=False,

        encoding="utf-8-sig"

    )


    print(

        "Arquivo gerado:",

        caminho_saida

    )


    for aviso in df_saida.attrs.get(

        "avisos",

        []

    ):

        print(

            "AVISO:",

            aviso

        )