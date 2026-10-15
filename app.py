from flask import Flask, render_template, request, send_file

from leitoritau import ler_extrato_itau
from leitor_inteligente import ler_extrato_inteligente
from itau_modelo2 import ler_itau_modelo2
from itau_aplicacao import ler_itau_aplicacao
from bradesco_unificado import ler_bradesco_unificado
from alooh_excel import ler_alooh_excel
from cibi_aplicacao import ler_cibi_aplicacao


# LAYOUTS FINAIS

from layout_serva import gerar_layout_serva
from layout_casa_cuidados_itau import gerar_layout_casa_cuidados_itau
from layout_ds import gerar_layout_ds

import os
import shutil


app = Flask(__name__)


# =====================================
# PASTAS
# =====================================

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
# LEITOR DE EXTRATO
# =====================================

@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )


# =====================================
# TELA DA EMPRESA
# LEITOR DE EXTRATO
# =====================================

@app.route("/empresa/<nome>")
def empresa(nome):

    return render_template(
        "leitorextrato.html",
        empresa=nome
    )


# =====================================
# TELA INICIAL
# LAYOUT FINAL
# =====================================

@app.route("/layout-final")
def layout_final():

    return render_template(
        "layout_final.html"
    )


# =====================================
# TELA DA EMPRESA
# LAYOUT FINAL
# =====================================

@app.route("/layout-final/<nome>")
def layout_empresa(nome):

    return render_template(
        "layout_empresa.html",
        empresa=nome
    )


# =====================================
# PROCESSAMENTO
# LEITOR DE EXTRATO
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
        # CIBI - APLICAÇÃO AUT MAIS
        # -----------------------------

        elif empresa == "cibi_aplicacao":

            print(
                "USANDO LEITOR CIBI APLICAÇÃO"
            )

            try:

                df = ler_cibi_aplicacao(
                    caminho_arquivo
                )

            except Exception as erro:

                print(
                    "ERRO NA CIBI APLICAÇÃO:",
                    erro
                )

                return (
                    "Erro durante a leitura "
                    "da CIBI Aplicação: "
                    f"{erro}"
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
    # ORGANIZA COLUNAS
    # CIBI APLICAÇÃO
    # =====================================

    if empresa == "cibi_aplicacao":

        colunas_desejadas = [
            "DATA",
            "aplicações",
            "valor principal resgatado",
            "iof",
            "irrf"
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

        nome_original = os.path.basename(
            arquivo.filename
        )

        nome_sem_extensao = os.path.splitext(
            nome_original
        )[0]

        nome_saida = (
            f"{nome_sem_extensao}.csv"
        )


    elif empresa == "cibi_aplicacao":

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
# PROCESSAMENTO DO LAYOUT FINAL
# =====================================

@app.route(
    "/processar-layout",
    methods=["POST"]
)
def processar_layout():

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
        "LAYOUT FINAL - EMPRESA:",
        empresa
    )


    # =====================================
    # VALIDAÇÕES
    # =====================================

    if not arquivo:

        return (
            "Nenhum arquivo enviado "
            "para o Layout Final."
        )

    if not empresa:

        return (
            "Empresa não identificada "
            "no Layout Final."
        )


    # =====================================
    # SALVA O ARQUIVO CONFERIDO
    # =====================================

    caminho_arquivo = os.path.join(
        PASTA_UPLOAD,
        arquivo.filename
    )

    arquivo.save(
        caminho_arquivo
    )


    # =====================================
    # SERVA
    # =====================================

    if empresa == "serva":

        print(
            "GERANDO LAYOUT FINAL SERVA"
        )

        try:

            resultado = gerar_layout_serva(
                caminho_arquivo
            )

        except Exception as erro:

            print(
                "ERRO NO LAYOUT SERVA:",
                erro
            )

            return (
                "Erro durante a geração "
                "do Layout Final da SERVA: "
                f"{erro}"
            )


        # =================================
        # VALIDA RESULTADO
        # =================================

        if resultado is None:

            return (
                "O Layout SERVA não retornou "
                "nenhum resultado."
            )


        if resultado.empty:

            return (
                "Nenhum lançamento foi gerado "
                "no Layout Final da SERVA."
            )


        # =================================
        # MOSTRA AVISOS NO LOG
        # =================================

        avisos = resultado.attrs.get(
            "avisos",
            []
        )


        if avisos:

            print(
                "====================================="
            )

            print(
                "AVISOS DO LAYOUT SERVA"
            )

            print(
                "====================================="
            )


            for aviso in avisos:

                print(
                    aviso
                )


        # =================================
        # NOME DO ARQUIVO FINAL
        # =================================

        nome_original = os.path.basename(
            arquivo.filename
        )

        nome_sem_extensao = os.path.splitext(
            nome_original
        )[0]

        nome_saida = (
            f"{nome_sem_extensao}"
            "_LAYOUT_SERVA.csv"
        )


        caminho_saida = os.path.join(
            PASTA_SAIDA,
            nome_saida
        )


        # =================================
        # GERA CSV FINAL
        # =================================

        try:

            resultado.to_csv(
                caminho_saida,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )

        except PermissionError:

            return (
                "O arquivo de saída está aberto. "
                "Feche o arquivo no Excel "
                "e tente novamente."
            )

        except Exception as erro:

            print(
                "ERRO AO GERAR CSV SERVA:",
                erro
            )

            return (
                "Erro ao gerar o arquivo "
                "final da SERVA: "
                f"{erro}"
            )


        # =================================
        # DOWNLOAD
        # =================================

        return send_file(
            caminho_saida,
            as_attachment=True,
            download_name=nome_saida
        )


    # =====================================
    # CASA DE CUIDADOS - ITAÚ
    # =====================================

    if empresa == "casa_cuidados_itau":

        print(
            "GERANDO LAYOUT FINAL "
            "CASA DE CUIDADOS ITAU"
        )

        try:

            resultado = (
                gerar_layout_casa_cuidados_itau(
                    caminho_arquivo
                )
            )

        except Exception as erro:

            print(
                "ERRO NO LAYOUT "
                "CASA DE CUIDADOS ITAU:",
                erro
            )

            return (
                "Erro durante a geração "
                "do Layout Final da "
                "Casa de Cuidados Itaú: "
                f"{erro}"
            )


        # =================================
        # VALIDA RESULTADO
        # =================================

        if resultado is None:

            return (
                "O Layout da Casa de "
                "Cuidados Itaú não retornou "
                "nenhum resultado."
            )


        if resultado.empty:

            return (
                "Nenhum lançamento foi "
                "gerado no Layout Final da "
                "Casa de Cuidados Itaú."
            )


        # =================================
        # NOME DO ARQUIVO FINAL
        # =================================

        nome_original = os.path.basename(
            arquivo.filename
        )

        nome_sem_extensao = os.path.splitext(
            nome_original
        )[0]

        nome_saida = (
            f"{nome_sem_extensao}"
            "_LAYOUT_CASA_CUIDADOS_ITAU.csv"
        )


        caminho_saida = os.path.join(
            PASTA_SAIDA,
            nome_saida
        )
            # =====================================
    # DS - BRADESCO
    # =====================================

    if empresa == "ds":

        print(
            "GERANDO LAYOUT FINAL DS"
        )

        try:

            resultado = gerar_layout_ds(
                caminho_arquivo
            )

        except Exception as erro:

            print(
                "ERRO NO LAYOUT DS:",
                erro
            )

            return (
                "Erro durante a geração "
                "do Layout Final da DS: "
                f"{erro}"
            )


        # =================================
        # VALIDA RESULTADO
        # =================================

        if resultado is None:

            return (
                "O Layout DS não retornou "
                "nenhum resultado."
            )


        if resultado.empty:

            return (
                "Nenhum lançamento foi gerado "
                "no Layout Final da DS."
            )


        # =================================
        # CONFERÊNCIA NO TERMINAL
        # =================================

        print(
            "DÉBITOS:",
            resultado.attrs.get(
                "quantidade_debitos",
                0
            )
        )

        print(
            "CRÉDITOS:",
            resultado.attrs.get(
                "quantidade_creditos",
                0
            )
        )

        print(
            "TOTAL:",
            resultado.attrs.get(
                "quantidade_total",
                len(resultado)
            )
        )


        # =================================
        # NOME DO ARQUIVO FINAL
        # =================================

        nome_original = os.path.basename(
            arquivo.filename
        )

        nome_sem_extensao = os.path.splitext(
            nome_original
        )[0]

        nome_saida = (
            f"{nome_sem_extensao}"
            "_LAYOUT_DS.csv"
        )


        caminho_saida = os.path.join(
            PASTA_SAIDA,
            nome_saida
        )


        # =================================
        # GERA CSV FINAL
        # =================================

        try:

            resultado.to_csv(
                caminho_saida,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )

        except PermissionError:

            return (
                "O arquivo de saída está aberto. "
                "Feche o arquivo no Excel "
                "e tente novamente."
            )

        except Exception as erro:

            print(
                "ERRO AO GERAR CSV DS:",
                erro
            )

            return (
                "Erro ao gerar o arquivo "
                "final da DS: "
                f"{erro}"
            )


        # =================================
        # DOWNLOAD
        # =================================

        return send_file(
            caminho_saida,
            as_attachment=True,
            download_name=nome_saida
        )







        








        # =================================
        # GERA CSV FINAL
        # =================================

        try:

            resultado.to_csv(
                caminho_saida,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )

        except PermissionError:

            return (
                "O arquivo de saída está aberto. "
                "Feche o arquivo no Excel "
                "e tente novamente."
            )

        except Exception as erro:

            print(
                "ERRO AO GERAR CSV "
                "CASA DE CUIDADOS ITAU:",
                erro
            )

            return (
                "Erro ao gerar o arquivo "
                "final da Casa de Cuidados Itaú: "
                f"{erro}"
            )


        # =================================
        # DOWNLOAD
        # =================================

        return send_file(
            caminho_saida,
            as_attachment=True,
            download_name=nome_saida
        )


    # =====================================
    # OUTRAS EMPRESAS
    # AINDA NÃO CONFIGURADAS
    # =====================================

    return (
        "Layout Final ainda não "
        f"configurado para: {empresa}"
    )


# =====================================
# INICIA O FLASK
# =====================================

if __name__ == "__main__":

    app.run()