from flask import Flask, render_template, request, send_file

from leitoritau import ler_extrato_itau
from leitor_inteligente import ler_extrato_inteligente
from itau_modelo2 import ler_itau_modelo2
from itau_aplicacao import ler_itau_aplicacao
from bradesco_unificado import ler_bradesco_unificado
from alooh_excel import ler_alooh_excel

import os
import shutil


app = Flask(__name__)


PASTA_UPLOAD = "uploads"
PASTA_SAIDA = "saidas"
PASTA_RECORTES = "recortes"


os.makedirs(
    PASTA_UPLOAD,
    exist_ok=True
)

os.makedirs(
    PASTA_SAIDA,
    exist_ok=True
)


# =====================================
# FORMATA VALORES NO PADRÃO BRASILEIRO
# =====================================

def formatar_br(valor):

    if valor is None:
        return ""

    if str(valor) == "nan":
        return ""

    if str(valor).strip() == "":
        return ""

    try:
        valor = float(valor)

    except (ValueError, TypeError):
        return str(valor)

    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# =====================================
# APAGA RECORTES DO OCR
# =====================================

def apagar_recortes():

    if os.path.exists(
        PASTA_RECORTES
    ):

        try:

            shutil.rmtree(
                PASTA_RECORTES
            )

            print(
                "RECORTES APAGADOS."
            )

        except Exception as erro:

            print(
                "ERRO AO APAGAR RECORTES:",
                erro
            )


# =====================================
# TELA INICIAL
# =====================================

@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )


# =====================================
# TELA DA EMPRESA
# =====================================

@app.route("/empresa/<nome>")
def empresa(nome):

    return render_template(
        "leitorextrato.html",
        empresa=nome
    )


# =====================================
# PROCESSAMENTO
# =====================================

@app.route(
    "/processar",
    methods=["POST"]
)
def processar():

    # =====================================
    # RECEBE ARQUIVO E EMPRESA
    # =====================================

    arquivo = request.files.get(
        "arquivo"
    )

    empresa = request.form.get(
        "empresa"
    )

    print(
        "EMPRESA RECEBIDA:",
        empresa
    )


    # =====================================
    # VALIDAÇÕES
    # =====================================

    if not arquivo:

        return (
            "Nenhum arquivo enviado."
        )

    if not empresa:

        return (
            "Empresa não identificada."
        )


    # =====================================
    # SALVA O ARQUIVO
    # =====================================

    caminho_arquivo = os.path.join(
        PASTA_UPLOAD,
        arquivo.filename
    )

    arquivo.save(
        caminho_arquivo
    )


    # =====================================
    # LEITURA INTELIGENTE
    # =====================================

    if empresa == "leitura_inteligente":

        print(
            "USANDO LEITURA INTELIGENTE"
        )

        try:

            df = ler_extrato_inteligente(
                caminho_arquivo
            )

        except Exception as erro:

            # Se der erro durante o OCR,
            # também apaga os recortes.

            apagar_recortes()

            print(
                "ERRO NA LEITURA INTELIGENTE:",
                erro
            )

            return (
                "Erro durante a leitura inteligente: "
                f"{erro}"
            )


    # =====================================
    # LEITURA NORMAL
    # =====================================

    else:

        # -----------------------------
        # ITAÚ MODELO NORMAL
        # -----------------------------

        if empresa in [
            "serva",
            "nrg",
            "globe",
            "wooh_midia",
            "casa_cuidados_itau"
        ]:

            print(
                "USANDO LEITOR ITAU NORMAL"
            )

            df = ler_extrato_itau(
                caminho_arquivo
            )


        # -----------------------------
        # CIBI - ITAÚ MODELO 2
        # -----------------------------

        elif empresa == "cibi":

            print(
                "USANDO LEITOR CIBI"
            )

            df = ler_itau_modelo2(
                caminho_arquivo
            )


        # -----------------------------
        # BRADESCO
        # -----------------------------

        elif empresa in [
            "ds",
            "casa_cuidados_bradesco"
        ]:

            print(
                "USANDO BRADESCO UNIFICADO"
            )

            df = ler_bradesco_unificado(
                caminho_arquivo
            )


        # -----------------------------
        # TODAS AS SUKYO
        # -----------------------------

        elif empresa.startswith(
            "sukyo_"
        ):

            print(
                "USANDO ITAU APLICACAO"
            )

            df = ler_itau_aplicacao(
                caminho_arquivo
            )


        # -----------------------------
        # ALOOH MIDIA - EXCEL
        # -----------------------------

        elif empresa == "alooh_midia":

            print(
                "USANDO LEITOR EXCEL ALOOH"
            )

            df = ler_alooh_excel(
                caminho_arquivo
            )


        # -----------------------------
        # EMPRESA SEM LEITOR
        # -----------------------------

        else:

            return (
                "Leitor ainda não "
                f"configurado para: {empresa}"
            )


    # =====================================
    # VALIDA RESULTADO
    # =====================================

    if df is None:

        if empresa == "leitura_inteligente":
            apagar_recortes()

        return (
            "O leitor não retornou "
            "nenhum resultado."
        )

    if df.empty:

        if empresa == "leitura_inteligente":
            apagar_recortes()

        return (
            "Nenhum lançamento "
            "foi encontrado."
        )


    # =====================================
    # FORMATA DÉBITO E CRÉDITO
    # SOMENTE NOS LEITORES NORMAIS
    # =====================================

    if empresa != "leitura_inteligente":

        if "Débito" in df.columns:

            df["Débito"] = (
                df["Débito"]
                .apply(
                    formatar_br
                )
            )

        if "Crédito" in df.columns:

            df["Crédito"] = (
                df["Crédito"]
                .apply(
                    formatar_br
                )
            )


    # =====================================
    # ORGANIZA COLUNAS
    # LEITURA INTELIGENTE
    # =====================================

    if empresa == "leitura_inteligente":

        colunas_desejadas = [
            "Data",
            "Histórico",
            "Crédito",
            "Débito",
            "Status"
        ]

        colunas_existentes = [
            coluna
            for coluna in colunas_desejadas
            if coluna in df.columns
        ]

        df = df[
            colunas_existentes
        ].copy()


    # =====================================
    # NOME DO CSV
    # =====================================

    if empresa == "leitura_inteligente":

        # Exemplo:
        #
        # Extrato Itau Setembro.pdf
        #
        # vira:
        #
        # Extrato Itau Setembro.csv

        nome_original = os.path.basename(
            arquivo.filename
        )

        nome_sem_extensao = os.path.splitext(
            nome_original
        )[0]

        nome_saida = (
            f"{nome_sem_extensao}.csv"
        )

    else:

        nome_saida = (
            f"{empresa.replace('_', ' ').upper()}.csv"
        )


    caminho_csv = os.path.join(
        PASTA_SAIDA,
        nome_saida
    )


    # =====================================
    # GERA CSV
    # =====================================

    try:

        df.to_csv(
            caminho_csv,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

    except PermissionError:

        if empresa == "leitura_inteligente":
            apagar_recortes()

        return (
            "O arquivo de saída está aberto. "
            "Feche o arquivo no Excel "
            "e tente novamente."
        )

    except Exception as erro:

        if empresa == "leitura_inteligente":
            apagar_recortes()

        return (
            "Erro ao gerar o CSV: "
            f"{erro}"
        )


    # =====================================
    # APAGA RECORTES DA LEITURA INTELIGENTE
    # =====================================

    if empresa == "leitura_inteligente":

        apagar_recortes()


    # =====================================
    # DOWNLOAD
    # =====================================

    return send_file(
        caminho_csv,
        as_attachment=True,
        download_name=nome_saida
    )


# =====================================
# INICIA O FLASK
# =====================================

if __name__ == "__main__":

    app.run()