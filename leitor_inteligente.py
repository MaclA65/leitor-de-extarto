import pymupdf
import pandas as pd
import base64
import json

from pathlib import Path
from openai import OpenAI




def recortar_paginas(caminho_pdf):

    documento = pymupdf.open(caminho_pdf)

    pasta_saida = Path("recortes")
    pasta_saida.mkdir(exist_ok=True)

    arquivos_recortados = []

    for numero, pagina in enumerate(documento, start=1):

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
            matrix=pymupdf.Matrix(2, 2),
            alpha=False
        )

        caminho_imagem = (
            pasta_saida
            / f"pagina_{numero}.png"
        )

        pix.save(
            str(caminho_imagem)
        )

        arquivos_recortados.append(
            str(caminho_imagem)
        )

    documento.close()

    return arquivos_recortados


def imagem_para_base64(caminho_imagem):

    with open(caminho_imagem, "rb") as arquivo:

        imagem_base64 = base64.b64encode(
            arquivo.read()
        ).decode("utf-8")

    return imagem_base64


def ler_pagina_com_ia(caminho_imagem):
    client = OpenAI()

    imagem_base64 = imagem_para_base64(
        caminho_imagem
    )

    resposta = client.responses.create(

        model="gpt-5.6-sol",

        input=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "input_text",
                        "text": """
Você é um especialista em extratos bancários
brasileiros.

Analise somente a tabela de movimentações
bancárias desta imagem.

Extraia cada lançamento individualmente.

Retorne SOMENTE JSON válido.

Formato obrigatório:

[
    {
        "data": "DD/MM/AAAA",
        "historico": "descrição completa",
        "credito": 0.00,
        "debito": null
    },
    {
        "data": "DD/MM/AAAA",
        "historico": "descrição completa",
        "credito": null,
        "debito": 0.00
    }
]

REGRAS:

- Crédito deve ser número positivo.
- Débito deve ser número positivo.
- Nunca colocar sinal negativo.
- Se for crédito, débito deve ser null.
- Se for débito, crédito deve ser null.
- Preserve o histórico da movimentação.
- Não some lançamentos do mesmo dia.
- Cada lançamento deve permanecer separado.
- Não incluir saldo anterior.
- Não incluir saldo final.
- Não incluir totais.
- Não incluir resumo financeiro.
- Não incluir investimentos.
- Não inventar informações.
- Se uma linha não estiver legível,
  ignore essa linha.
"""
                    },

                    {
                        "type": "input_image",
                        "image_url":
                            "data:image/png;base64,"
                            + imagem_base64
                    }
                ]
            }
        ]
    )

    texto = resposta.output_text

    print(
        "RESPOSTA DA IA:"
    )

    print(
        texto
    )

    # remove possíveis blocos markdown
    texto = texto.replace(
        "```json",
        ""
    )

    texto = texto.replace(
        "```",
        ""
    )

    texto = texto.strip()

    dados = json.loads(
        texto
    )

    return dados


def ler_extrato_inteligente(caminho_arquivo):

    imagens = recortar_paginas(
        caminho_arquivo
    )

    todos_registros = []

    for imagem in imagens:

        print(
            "LENDO COM IA:",
            imagem
        )

        try:

            registros = ler_pagina_com_ia(
                imagem
            )

            todos_registros.extend(
                registros
            )

        except Exception as erro:

            print(
                "ERRO NA PÁGINA:",
                imagem
            )

            print(
                erro
            )

    df = pd.DataFrame(
        todos_registros
    )


    if df.empty:

        return pd.DataFrame(
            columns=[
                "Data",
                "Histórico",
                "Crédito",
                "Débito"
            ]
        )


    df = df.rename(
        columns={
            "data": "Data",
            "historico": "Histórico",
            "credito": "Crédito",
            "debito": "Débito"
        }
    )


    colunas = [
        "Data",
        "Histórico",
        "Crédito",
        "Débito"
    ]

    for coluna in colunas:

        if coluna not in df.columns:

            df[coluna] = None


    df = df[
        colunas
    ]


    return df