import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
import pymupdf
import pytesseract

from PIL import Image


# ============================================================
# TESSERACT
# ============================================================

CAMINHO_TESSERACT_WINDOWS = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if CAMINHO_TESSERACT_WINDOWS.exists():
    pytesseract.pytesseract.tesseract_cmd = str(
        CAMINHO_TESSERACT_WINDOWS
    )


# ============================================================
# NORMALIZA TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return texto


# ============================================================
# RECORTA AS PÁGINAS
# ============================================================

def recortar_paginas(caminho_pdf):

    documento = pymupdf.open(
        caminho_pdf
    )

    pasta = Path(
        "recortes"
    )

    pasta.mkdir(
        exist_ok=True
    )

    imagens = []

    for numero, pagina in enumerate(
        documento,
        start=1
    ):

        largura = pagina.rect.width
        altura = pagina.rect.height

        area = pymupdf.Rect(
            largura * 0.05,
            altura * 0.18,
            largura * 0.95,
            altura * 0.90
        )

        pix = pagina.get_pixmap(
            clip=area,
            matrix=pymupdf.Matrix(
                3,
                3
            ),
            alpha=False
        )

        caminho = (
            pasta
            / f"pagina_{numero}.png"
        )

        pix.save(
            str(caminho)
        )

        imagens.append(
            str(caminho)
        )

    documento.close()

    return imagens


# ============================================================
# OCR
# ============================================================

def ler_pagina_com_ocr(caminho_imagem):

    imagem = Image.open(
        caminho_imagem
    )

    largura = imagem.width

    dados = pytesseract.image_to_data(
        imagem,
        lang="por",
        output_type=pytesseract.Output.DATAFRAME
    )

    imagem.close()

    return dados, largura


# ============================================================
# LIMPA OCR
# ============================================================

def limpar_dados_ocr(dados):

    dados = dados.copy()

    dados = dados[
        dados["text"].notna()
    ].copy()

    dados["text"] = (
        dados["text"]
        .astype(str)
        .str.strip()
    )

    dados = dados[
        dados["text"] != ""
    ].copy()

    dados["texto_normalizado"] = (
        dados["text"]
        .apply(normalizar_texto)
    )

    return dados


# ============================================================
# DATA
# ============================================================

def extrair_data(texto):

    resultado = re.search(
        r"\b(\d{2}/\d{2})\b",
        str(texto)
    )

    if resultado:
        return resultado.group(1)

    return ""


# ============================================================
# INDÍCIO NUMÉRICO
# ============================================================

def tem_indicio_numerico(texto):

    if texto is None:
        return False

    digitos = re.sub(
        r"\D",
        "",
        str(texto)
    )

    return len(digitos) >= 2


# ============================================================
# VALOR MONETÁRIO SEGURO
# ============================================================

def limpar_valor_seguro(valor):

    if valor is None:
        return ""

    valor = str(
        valor
    ).strip()

    valor = re.sub(
        r"[^0-9.,]",
        "",
        valor
    )

    if not valor:
        return ""

    while valor.startswith("."):
        valor = valor[1:]

    while valor.endswith("."):
        valor = valor[:-1]

    # 167.69 -> 167,69
    if re.fullmatch(
        r"\d+\.\d{2}",
        valor
    ):

        inteiro, centavos = valor.rsplit(
            ".",
            1
        )

        valor = (
            inteiro
            + ","
            + centavos
        )

    # 2.881,78
    # 70.956,99
    # 163,96
    if re.fullmatch(
        r"\d{1,3}(?:\.\d{3})*,\d{2}",
        valor
    ):
        return valor

    # 1458,36
    if re.fullmatch(
        r"\d+,\d{2}",
        valor
    ):
        return valor

    return ""


# ============================================================
# IDENTIFICA NÚMERO DE SEQUÊNCIA / DOCUMENTO
# ============================================================

def eh_numero_sequencia(texto):

    texto = str(
        texto
    ).strip()

    # Exemplo:
    # 1210035
    # 0009283
    # 9174809
    # 5960051
    #
    # São números isolados de 7 dígitos.
    if re.fullmatch(
        r"\d{7}",
        texto
    ):
        return True

    return False


# ============================================================
# LIMPA HISTÓRICO
# ============================================================

def limpar_historico(texto):

    if not texto:
        return ""

    partes = str(
        texto
    ).split()

    resultado = []

    ruidos = {
        "|",
        "||",
        "=",
        "+",
        "—",
        "Ê"
    }

    for parte in partes:

        parte_limpa = (
            parte
            .strip()
            .strip(".,;:")
        )

        # --------------------------------------------
        # RUÍDO
        # --------------------------------------------

        if parte in ruidos:
            continue

        if parte.lower() in {
            "o",
            "e"
        }:
            continue

        # --------------------------------------------
        # NÚMERO DE SEQUÊNCIA / DOCUMENTO
        #
        # 1210035
        # 0009283
        # 9174809
        #
        # NÃO vai para o Histórico.
        # --------------------------------------------

        if eh_numero_sequencia(
            parte_limpa
        ):
            continue

        resultado.append(
            parte
        )

    texto_final = " ".join(
        resultado
    ).strip()

    # Remove espaços duplicados.
    texto_final = re.sub(
        r"\s+",
        " ",
        texto_final
    )

    return texto_final


# ============================================================
# AGRUPA OCR POR LINHA
# ============================================================

def agrupar_linhas(dados):

    dados = limpar_dados_ocr(
        dados
    )

    dados = dados.sort_values(
        [
            "page_num",
            "block_num",
            "par_num",
            "line_num",
            "word_num"
        ]
    )

    linhas = []

    grupos = dados.groupby(
        [
            "page_num",
            "block_num",
            "par_num",
            "line_num"
        ],
        sort=False
    )

    for _, grupo in grupos:

        grupo = grupo.sort_values(
            "left"
        )

        palavras = []

        for _, item in grupo.iterrows():

            palavras.append(
                {
                    "texto": str(
                        item["text"]
                    ).strip(),

                    "left": int(
                        item["left"]
                    ),

                    "right": int(
                        item["left"]
                        + item["width"]
                    )
                }
            )

        texto = " ".join(
            item["texto"]
            for item in palavras
        )

        linhas.append(
            {
                "top": int(
                    grupo["top"].min()
                ),

                "bottom": int(
                    (
                        grupo["top"]
                        + grupo["height"]
                    ).max()
                ),

                "texto": texto,

                "palavras": palavras
            }
        )

    return sorted(
        linhas,
        key=lambda x: x["top"]
    )


# ============================================================
# LOCALIZA CABEÇALHO
# ============================================================

def localizar_cabecalho(
    dados,
    largura
):

    dados = limpar_dados_ocr(
        dados
    )

    candidatos_data = dados[
        dados["texto_normalizado"]
        == "data"
    ]

    if candidatos_data.empty:
        return None

    for _, item_data in candidatos_data.iterrows():

        top_data = int(
            item_data["top"]
        )

        faixa = dados[
            (
                dados["top"]
                >= top_data - 20
            )
            &
            (
                dados["top"]
                <= top_data + 20
            )
        ].copy()

        posicoes = {
            "data": int(
                item_data["left"]
            )
        }

        candidatos = faixa[
            faixa["texto_normalizado"]
            .str.startswith(
                "histor"
            )
        ]

        if not candidatos.empty:
            posicoes["historico"] = int(
                candidatos["left"].min()
            )

        candidatos = faixa[
            faixa["texto_normalizado"]
            .str.startswith(
                "docto"
            )
        ]

        if not candidatos.empty:
            posicoes["docto"] = int(
                candidatos["left"].min()
            )

        candidatos = faixa[
            faixa["texto_normalizado"]
            .str.startswith(
                "credit"
            )
        ]

        if not candidatos.empty:
            posicoes["credito"] = int(
                candidatos["left"].min()
            )

        candidatos = faixa[
            faixa["texto_normalizado"]
            .str.startswith(
                "debit"
            )
        ]

        if not candidatos.empty:
            posicoes["debito"] = int(
                candidatos["left"].min()
            )

        if "debito" in posicoes:

            candidatos_saldo = faixa[
                (
                    faixa[
                        "texto_normalizado"
                    ]
                    == "saldo"
                )
                &
                (
                    faixa["left"]
                    > posicoes["debito"]
                )
            ]

            if not candidatos_saldo.empty:

                posicoes["saldo"] = int(
                    candidatos_saldo[
                        "left"
                    ].max()
                )

        if (
            "historico" not in posicoes
            or "credito" not in posicoes
            or "debito" not in posicoes
        ):
            continue

        if "docto" not in posicoes:

            posicoes["docto"] = int(
                (
                    posicoes["historico"]
                    + posicoes["credito"]
                )
                / 2
            )

        if "saldo" not in posicoes:

            posicoes["saldo"] = int(
                largura * 0.90
            )

        if (
            posicoes["saldo"]
            <= posicoes["debito"]
        ):

            posicoes["saldo"] = int(
                largura * 0.90
            )

        if not (
            posicoes["historico"]
            < posicoes["docto"]
            < posicoes["credito"]
            < posicoes["debito"]
            < posicoes["saldo"]
        ):
            continue

        bottom = int(
            (
                faixa["top"]
                + faixa["height"]
            ).max()
        )

        return {
            "posicoes": posicoes,
            "bottom": bottom
        }

    return None


# ============================================================
# FALLBACK
# ============================================================

def criar_posicoes_fallback(largura):

    return {
        "data": int(
            largura * 0.03
        ),

        "historico": int(
            largura * 0.23
        ),

        "docto": int(
            largura * 0.46
        ),

        "credito": int(
            largura * 0.58
        ),

        "debito": int(
            largura * 0.74
        ),

        "saldo": int(
            largura * 0.90
        )
    }


# ============================================================
# ÁREA DE INVESTIMENTOS
# ============================================================

def eh_inicio_area_investimentos(texto):

    texto_original = str(
        texto
    )

    texto_norm = normalizar_texto(
        texto_original
    )

    marcadores = [
        "total de rendimento tributavel",
        "total de imposto de renda",
        "comprovante de rendimentos",
        "informe de rendimentos",
        "demonstrativo de investimentos",
        "extrato de investimentos"
    ]

    if any(
        marcador in texto_norm
        for marcador in marcadores
    ):
        return True

    datas_completas = re.findall(
        r"\b\d{2}/\d{2}/\d{4}\b",
        texto_original
    )

    datas_compactas = re.findall(
        r"\b\d{8}\b",
        texto_original
    )

    taxas = re.findall(
        r"\b\d+[.,]\d{4}\b",
        texto_original
    )

    quantidade_datas = (
        len(datas_completas)
        + len(datas_compactas)
    )

    if (
        quantidade_datas >= 2
        and len(taxas) >= 1
    ):
        return True

    return False


# ============================================================
# NOVO LANÇAMENTO
# ============================================================

def eh_inicio_lancamento(historico):

    if not historico:
        return False

    texto = normalizar_texto(
        historico
    )

    termos = [
        "ted",
        "transf",
        "resgate",
        "rentab",
        "pagto",
        "pagao",
        "pago",
        "eletron",
        "liquidacao",
        "tarifa",
        "conta de luz",
        "conta de agua",
        "conta de telefone",
        "conta de gas",
        "pix",
        "aplicacao"
    ]

    return any(
        termo in texto
        for termo in termos
    )


# ============================================================
# COMPLEMENTO DE HISTÓRICO
# ============================================================

def eh_complemento_historico(historico):

    texto = normalizar_texto(
        historico
    ).strip()

    if not texto:
        return False

    complementos = [
        "rem:",
        "remet:",
        "des:",
        "dest:",
        "benef:",
        "fav:",
        "favorecido"
    ]

    if any(
        texto.startswith(item)
        for item in complementos
    ):
        return True

    if texto in {
        "ted internet",
        "transf pgto pix"
    }:
        return True

    return False


# ============================================================
# STATUS
# ============================================================

def definir_status(
    historico,
    credito,
    debito,
    credito_bruto,
    debito_bruto
):

    if credito or debito:
        return "OK"

    if (
        tem_indicio_numerico(
            credito_bruto
        )
        or
        tem_indicio_numerico(
            debito_bruto
        )
    ):
        return "REVISAR"

    if eh_inicio_lancamento(
        historico
    ):
        return "NÃO CONFIÁVEL"

    return ""


# ============================================================
# SEPARA MOVIMENTOS
# ============================================================

def separar_movimentos(
    dados,
    largura,
    posicoes_anteriores=None
):

    dados = limpar_dados_ocr(
        dados
    )

    cabecalho = localizar_cabecalho(
        dados,
        largura
    )

    if cabecalho is not None:

        posicoes = cabecalho[
            "posicoes"
        ]

        inicio_y = cabecalho[
            "bottom"
        ]

        print(
            "CABEÇALHO ENCONTRADO:",
            posicoes
        )

    elif posicoes_anteriores is not None:

        posicoes = (
            posicoes_anteriores.copy()
        )

        inicio_y = 0

        print(
            "SEM CABEÇALHO."
        )

        print(
            "REUTILIZANDO POSIÇÕES:",
            posicoes
        )

    else:

        posicoes = (
            criar_posicoes_fallback(
                largura
            )
        )

        inicio_y = 0

        print(
            "USANDO POSIÇÕES FALLBACK:",
            posicoes
        )

    x_docto = (
        posicoes["docto"]
    )

    x_credito = (
        posicoes["credito"]
    )

    x_debito = (
        posicoes["debito"]
    )

    x_saldo = (
        posicoes["saldo"]
    )

    if x_saldo <= x_debito:

        x_saldo = int(
            largura * 0.90
        )

        posicoes["saldo"] = (
            x_saldo
        )

    print(
        "FAIXA CRÉDITO:",
        x_credito,
        "até",
        x_debito
    )

    print(
        "FAIXA DÉBITO:",
        x_debito,
        "até",
        x_saldo
    )

    linhas = agrupar_linhas(
        dados
    )

    registros = []

    dentro_tabela = (
        cabecalho is not None
    )

    encontrou_fim = False

    for linha in linhas:

        if (
            cabecalho is not None
            and linha["top"] <= inicio_y
        ):
            continue

        texto_completo = (
            linha["texto"]
        )

        texto_norm = normalizar_texto(
            texto_completo
        )

        if eh_inicio_area_investimentos(
            texto_completo
        ):

            print(
                "FIM DA MOVIMENTAÇÃO "
                "DE CONTA-CORRENTE DETECTADO:"
            )

            print(
                texto_completo
            )

            encontrou_fim = True

            break

        if any(
            termo in texto_norm
            for termo in [
                "resumo financeiro",
                "saldo conta facil",
                "total disponivel",
                "total geral",
                "limite credito"
            ]
        ):
            continue

        if (
            "saldo anterior"
            in texto_norm
        ):
            continue

        if (
            "historico" in texto_norm
            and "credito" in texto_norm
        ):

            dentro_tabela = True
            continue

        if not dentro_tabela:

            if (
                eh_inicio_lancamento(
                    texto_completo
                )
                or
                extrair_data(
                    texto_completo
                )
            ):

                dentro_tabela = True

            else:
                continue

        data = extrair_data(
            texto_completo
        )

        historico = []

        credito_bruto = []

        debito_bruto = []

        for palavra in linha[
            "palavras"
        ]:

            texto = palavra[
                "texto"
            ]

            left = palavra[
                "left"
            ]

            if re.fullmatch(
                r"\d{2}/\d{2}",
                texto
            ):
                continue

            if left < x_docto:

                historico.append(
                    texto
                )

            elif (
                left >= x_docto
                and left < x_credito
            ):

                continue

            elif (
                left >= x_credito
                and left < x_debito
            ):

                credito_bruto.append(
                    texto
                )

            elif (
                left >= x_debito
                and left < x_saldo
            ):

                debito_bruto.append(
                    texto
                )

        historico = limpar_historico(
            " ".join(
                historico
            )
        )

        credito_bruto_texto = " ".join(
            credito_bruto
        ).strip()

        debito_bruto_texto = " ".join(
            debito_bruto
        ).strip()

        credito = limpar_valor_seguro(
            credito_bruto_texto
        )

        debito = limpar_valor_seguro(
            debito_bruto_texto
        )

        status = definir_status(
            historico,
            credito,
            debito,
            credito_bruto_texto,
            debito_bruto_texto
        )

        if (
            data
            or historico
            or credito
            or debito
        ):

            registros.append(
                {
                    "Data": data,

                    "Histórico": historico,

                    "Crédito": credito,

                    "Débito": debito,

                    "_CreditoBruto": (
                        credito_bruto_texto
                    ),

                    "_DebitoBruto": (
                        debito_bruto_texto
                    ),

                    "_Status": status
                }
            )

    return (
        registros,
        posicoes,
        encontrou_fim
    )


# ============================================================
# CONSOLIDA
# ============================================================

def consolidar_lancamentos(
    registros,
    data_inicial=""
):

    resultado = []

    data_atual = (
        data_inicial
    )

    lancamento_atual = None

    for registro in registros:

        data = registro[
            "Data"
        ].strip()

        historico = registro[
            "Histórico"
        ].strip()

        credito = registro[
            "Crédito"
        ].strip()

        debito = registro[
            "Débito"
        ].strip()

        status = registro[
            "_Status"
        ].strip()

        bruto_credito = registro[
            "_CreditoBruto"
        ]

        bruto_debito = registro[
            "_DebitoBruto"
        ]

        if data:
            data_atual = data

        tem_valor = bool(
            credito
            or debito
        )

        tem_indicio = (
            tem_indicio_numerico(
                bruto_credito
            )
            or
            tem_indicio_numerico(
                bruto_debito
            )
        )

        inicio = (
            eh_inicio_lancamento(
                historico
            )
        )

        complemento = (
            eh_complemento_historico(
                historico
            )
        )

        if (
            complemento
            and not tem_valor
            and not tem_indicio
            and lancamento_atual is not None
        ):

            lancamento_atual[
                "Histórico"
            ] = (
                lancamento_atual[
                    "Histórico"
                ]
                + " "
                + historico
            ).strip()

            continue

        if (
            tem_valor
            or tem_indicio
            or inicio
        ):

            if not status:
                status = (
                    "NÃO CONFIÁVEL"
                )

            novo = {
                "Data": data_atual,
                "Histórico": historico,
                "Crédito": credito,
                "Débito": debito,
                "Status": status
            }

            resultado.append(
                novo
            )

            lancamento_atual = novo

            continue

        if (
            historico
            and lancamento_atual is not None
        ):

            lancamento_atual[
                "Histórico"
            ] = (
                lancamento_atual[
                    "Histórico"
                ]
                + " "
                + historico
            ).strip()

    return (
        resultado,
        data_atual
    )


# ============================================================
# DESCOBRE MÊS PRINCIPAL
# ============================================================

def descobrir_mes_principal(lancamentos):

    meses = []

    for item in lancamentos:

        data = str(
            item.get(
                "Data",
                ""
            )
        )

        resultado = re.fullmatch(
            r"\d{2}/(\d{2})",
            data
        )

        if resultado:

            meses.append(
                resultado.group(1)
            )

    if not meses:
        return None

    return max(
        set(meses),
        key=meses.count
    )


# ============================================================
# FILTRA MÊS
# ============================================================

def filtrar_mes_principal(df):

    if df.empty:
        return df

    mes_principal = (
        descobrir_mes_principal(
            df.to_dict(
                "records"
            )
        )
    )

    if not mes_principal:
        return df

    print(
        "MÊS PRINCIPAL IDENTIFICADO:",
        mes_principal
    )

    manter = []

    for _, linha in df.iterrows():

        data = str(
            linha["Data"]
        ).strip()

        resultado = re.fullmatch(
            r"\d{2}/(\d{2})",
            data
        )

        if not resultado:

            manter.append(
                True
            )

            continue

        manter.append(
            resultado.group(1)
            == mes_principal
        )

    return (
        df[
            manter
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


# ============================================================
# LEITOR INTELIGENTE
# ============================================================

def ler_extrato_inteligente(
    caminho_arquivo
):

    imagens = recortar_paginas(
        caminho_arquivo
    )

    todos_lancamentos = []

    ultima_data = ""

    posicoes_principais = None

    parar_documento = False

    for numero, imagem in enumerate(
        imagens,
        start=1
    ):

        if parar_documento:
            break

        print(
            "\n=============================="
        )

        print(
            "LENDO PÁGINA:",
            numero
        )

        print(
            "=============================="
        )

        try:

            dados, largura = (
                ler_pagina_com_ocr(
                    imagem
                )
            )

            (
                registros,
                posicoes,
                encontrou_fim
            ) = separar_movimentos(
                dados,
                largura,
                posicoes_principais
            )

            if (
                posicoes_principais
                is None
            ):

                posicoes_principais = (
                    posicoes.copy()
                )

            (
                lancamentos,
                ultima_data
            ) = consolidar_lancamentos(
                registros,
                ultima_data
            )

            todos_lancamentos.extend(
                lancamentos
            )

            print(
                "LANÇAMENTOS ENCONTRADOS:",
                len(lancamentos)
            )

            if encontrou_fim:

                print(
                    "LEITURA DA CONTA-CORRENTE "
                    "ENCERRADA."
                )

                parar_documento = True

        except Exception as erro:

            print(
                "ERRO NA PÁGINA:",
                numero
            )

            print(
                erro
            )

    if not todos_lancamentos:

        return pd.DataFrame(
            columns=[
                "Data",
                "Histórico",
                "Crédito",
                "Débito",
                "Status"
            ]
        )

    df = pd.DataFrame(
        todos_lancamentos
    )

    df = df[
        [
            "Data",
            "Histórico",
            "Crédito",
            "Débito",
            "Status"
        ]
    ].copy()

    df = df[
        ~(
            (df["Histórico"] == "")
            & (df["Crédito"] == "")
            & (df["Débito"] == "")
        )
    ].copy()

    df = filtrar_mes_principal(
        df
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# SALVA CSV
# ============================================================

def salvar_csv_seguro(
    df,
    nome_base
):

    caminho = Path(
        nome_base
    )

    try:

        df.to_csv(
            caminho,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        return str(
            caminho
        )

    except PermissionError:

        horario = datetime.now().strftime(
            "%H%M%S"
        )

        novo_nome = (
            caminho.stem
            + "_"
            + horario
            + caminho.suffix
        )

        novo_caminho = (
            caminho.with_name(
                novo_nome
            )
        )

        df.to_csv(
            novo_caminho,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        return str(
            novo_caminho
        )


# ============================================================
# ARQUIVO DE REVISÃO
# ============================================================

def gerar_arquivo_revisao(df):

    if df.empty:

        return pd.DataFrame(
            columns=df.columns
        )

    revisao = df[
        df["Status"].isin(
            [
                "REVISAR",
                "NÃO CONFIÁVEL"
            ]
        )
    ].copy()

    ordem = {
        "NÃO CONFIÁVEL": 1,
        "REVISAR": 2
    }

    revisao["_ordem"] = (
        revisao["Status"]
        .map(ordem)
        .fillna(99)
    )

    revisao = (
        revisao
        .sort_values(
            [
                "_ordem",
                "Data"
            ]
        )
        .drop(
            columns=[
                "_ordem"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return revisao


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    caminho_pdf = (
        "Extrato Unificado 07-2026.PDF"
    )

    print(
        "INICIANDO LEITURA..."
    )

    df = ler_extrato_inteligente(
        caminho_pdf
    )

    print(
        "\n=============================="
    )

    print(
        "RESULTADO FINAL"
    )

    print(
        "==============================\n"
    )

    if df.empty:

        print(
            "Nenhum lançamento encontrado."
        )

    else:

        print(
            df.to_string(
                index=False
            )
        )

        arquivo_completo = (
            salvar_csv_seguro(
                df,
                "resultado_leitura_inteligente.csv"
            )
        )

        df_revisao = (
            gerar_arquivo_revisao(
                df
            )
        )

        arquivo_revisao = (
            salvar_csv_seguro(
                df_revisao,
                "resultado_revisar.csv"
            )
        )

        print(
            "\n=============================="
        )

        print(
            "RESUMO"
        )

        print(
            "=============================="
        )

        print(
            "OK:",
            int(
                (
                    df["Status"]
                    == "OK"
                ).sum()
            )
        )

        print(
            "REVISAR:",
            int(
                (
                    df["Status"]
                    == "REVISAR"
                ).sum()
            )
        )

        print(
            "NÃO CONFIÁVEL:",
            int(
                (
                    df["Status"]
                    == "NÃO CONFIÁVEL"
                ).sum()
            )
        )

        print(
            "\nARQUIVO COMPLETO:"
        )

        print(
            arquivo_completo
        )

        print(
            "\nARQUIVO PARA CONFERÊNCIA:"
        )

        print(
            arquivo_revisao
        )