from flask import Flask, render_template, request, send_file
from leitoritau import ler_extrato_itau
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


@app.route("/processar", methods=["POST"])
def processar():

    arquivo = request.files.get("arquivo")

    if not arquivo:
        return "Nenhum arquivo enviado."

    caminho_pdf = os.path.join(
        PASTA_UPLOAD,
        arquivo.filename
    )

    arquivo.save(caminho_pdf)

    df = ler_extrato_itau(caminho_pdf)

    df["Débito"] = df["Débito"].apply(formatar_br)
    df["Crédito"] = df["Crédito"].apply(formatar_br)

    caminho_csv = os.path.join(
        PASTA_SAIDA,
        "resultado_itau.csv"
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
    app.run(debug=True)