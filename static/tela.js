const pesquisaEmpresa =
    document.getElementById("pesquisaEmpresa");

const listaEmpresas =
    document.getElementById("listaEmpresas");

const empresas =
    document.querySelectorAll(".empresa-opcao");


pesquisaEmpresa.addEventListener("focus", () => {
    listaEmpresas.classList.add("aberta");
});


pesquisaEmpresa.addEventListener("input", () => {

    const texto =
        pesquisaEmpresa.value
            .toLowerCase()
            .trim();

    listaEmpresas.classList.add("aberta");

    empresas.forEach((empresa) => {

        const nome =
            empresa.dataset.nome
                .toLowerCase();

        if (nome.includes(texto)) {
            empresa.style.display = "block";
        } else {
            empresa.style.display = "none";
        }

    });

});


document.addEventListener("click", (event) => {

    const seletor =
        document.querySelector(".seletor-empresa");

    if (!seletor.contains(event.target)) {
        listaEmpresas.classList.remove("aberta");
    }

});