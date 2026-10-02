from flask import Flask, render_template, request, send_file
from leitoritau import ler_extrato_itau
from itau_modelo2 import ler_itau_modelo2
import os

app = Flask(__name__)

PASTA_UPLOAD = "uploads"
PASTA_SAIDA = "saidas"

os.makedirs(PASTA_UPLOAD, exist_ok=True)
os.makedirs(PASTA_SAIDA, exist_ok=True)


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


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/empresa/<nome>")
def empresa(nome):
    return render_template(
        "leitorextrato.html",
        empresa=nome
    )


@app.route("/processar", methods=["POST"])
def processar():

    arquivo = request.files.get("arquivo")
    empresa = request.form.get("empresa")

    if not arquivo:
        return "Nenhum arquivo enviado."

    if not empresa:
        return "Empresa não identificada."

    caminho_pdf = os.path.join(
        PASTA_UPLOAD,
        arquivo.filename
    )

    arquivo.save(caminho_pdf)

    # ESCOLHE QUAL LEITOR USAR
    if empresa == "serva":

        df = ler_extrato_itau(
            caminho_pdf
        )

    elif empresa == "cibi":

        df = ler_itau_modelo2(
            caminho_pdf
        )

    else:

        return f"Leitor ainda não configurado para: {empresa}"

    # FORMATA DÉBITO
    if "Débito" in df.columns:
        df["Débito"] = (
            df["Débito"]
            .apply(formatar_br)
        )

    # FORMATA CRÉDITO
    if "Crédito" in df.columns:
        df["Crédito"] = (
            df["Crédito"]
            .apply(formatar_br)
        )

    # NOME DO CSV
    nome_saida = f"resultado_{empresa}.csv"

    caminho_csv = os.path.join(
        PASTA_SAIDA,
        nome_saida
    )

    df.to_csv(
        caminho_csv,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    return send_file(
        caminho_csv,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run()