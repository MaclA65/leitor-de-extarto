document.addEventListener(
    "DOMContentLoaded",
    function () {

        configurarPesquisaEmpresas(
            "pesquisaEmpresa",
            "listaEmpresas"
        );

        configurarPesquisaEmpresas(
            "pesquisaEmpresaLayout",
            "listaEmpresasLayout"
        );

    }
);


function configurarPesquisaEmpresas(
    idPesquisa,
    idLista
) {

    const pesquisaEmpresa =
        document.getElementById(
            idPesquisa
        );

    const listaEmpresas =
        document.getElementById(
            idLista
        );


    if (
        !pesquisaEmpresa
        ||
        !listaEmpresas
    ) {

        return;

    }


    const empresas =
        listaEmpresas.querySelectorAll(
            ".empresa-opcao"
        );


    // =====================================
    // ABRE A LISTA AO CLICAR NA PESQUISA
    // =====================================

    pesquisaEmpresa.addEventListener(
        "focus",
        function () {

            listaEmpresas.classList.add(
                "aberta"
            );

        }
    );


    // =====================================
    // FILTRA AS EMPRESAS
    // =====================================

    pesquisaEmpresa.addEventListener(
        "input",
        function () {

            const texto =
                pesquisaEmpresa.value
                    .toLowerCase()
                    .trim();


            listaEmpresas.classList.add(
                "aberta"
            );


            empresas.forEach(
                function (empresa) {

                    const nome =
                        empresa
                            .dataset
                            .nome
                            .toLowerCase();


                    if (
                        nome.includes(
                            texto
                        )
                    ) {

                        empresa.style.display =
                            "block";

                    } else {

                        empresa.style.display =
                            "none";

                    }

                }
            );

        }
    );


    // =====================================
    // FECHA AO CLICAR FORA
    // =====================================

    document.addEventListener(
        "click",
        function (event) {

            const seletor =
                pesquisaEmpresa.closest(
                    ".seletor-empresa"
                );


            if (
                seletor
                &&
                !seletor.contains(
                    event.target
                )
            ) {

                listaEmpresas.classList.remove(
                    "aberta"
                );

            }

        }
    );

}