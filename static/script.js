const arquivo = document.getElementById("arquivo");
const selecionar = document.getElementById("selecionar");
const nomeArquivo = document.getElementById("nomeArquivo");
const processar = document.getElementById("processar");
const uploadBox = document.getElementById("uploadBox");
const resultado = document.getElementById("resultado");


selecionar.addEventListener("click", () => {
    arquivo.click();
});


arquivo.addEventListener("change", () => {
    if (arquivo.files.length > 0) {
        const file = arquivo.files[0];

        nomeArquivo.textContent =
            "Arquivo selecionado: " + file.name;

        processar.disabled = false;
    }
});


uploadBox.addEventListener("dragover", (event) => {
    event.preventDefault();

    uploadBox.classList.add("dragover");
});


uploadBox.addEventListener("dragleave", () => {
    uploadBox.classList.remove("dragover");
});


uploadBox.addEventListener("drop", (event) => {
    event.preventDefault();

    uploadBox.classList.remove("dragover");

    const files = event.dataTransfer.files;

    if (files.length > 0) {
        arquivo.files = files;

        nomeArquivo.textContent =
            "Arquivo selecionado: " + files[0].name;

        processar.disabled = false;
    }
});


processar.addEventListener("click", () => {
    if (resultado) {
        resultado.textContent =
            "Processando extrato...";
    }
});