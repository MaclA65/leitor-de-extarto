from flask import Flask, render_template, request, send_file

from leitoritau import ler_extrato_itau
from leitor_inteligente import ler_extrato_inteligente
from itau_modelo2 import ler_itau_modelo2
from itau_aplicacao import ler_itau_aplicacao
from bradesco_unificado import ler_bradesco_unificado
from alooh_excel import ler_alooh_excel

import os


app = Flask(__name__)


PASTA_UPLOAD = "uploads"
PASTA_SAIDA = "saidas"


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

    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
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

        df = ler_extrato_inteligente(
            caminho_arquivo
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
    # FORMATA DÉBITO
    # =====================================

    if "Débito" in df.columns:

        df["Débito"] = (
            df["Débito"]
            .apply(
                formatar_br
            )
        )


    # =====================================
    # FORMATA CRÉDITO
    # =====================================

    if "Crédito" in df.columns:

        df["Crédito"] = (
            df["Crédito"]
            .apply(
                formatar_br
            )
        )


    # =====================================
    # NOME DO CSV
    # =====================================

    if empresa == "leitura_inteligente":

        nome_saida = (
            "LEITURA INTELIGENTE.csv"
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

    df.to_csv(
        caminho_csv,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )


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