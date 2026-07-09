const botaoAdicionar = document.querySelector("#adicionar-nota");
const linhasNotas = document.querySelector("#linhas-notas");

if (botaoAdicionar && linhasNotas) {
    botaoAdicionar.addEventListener("click", () => {
        const primeiraLinha = linhasNotas.querySelector(".linha-nota");
        const novaLinha = primeiraLinha.cloneNode(true);

        novaLinha.querySelectorAll("input").forEach((campo) => {
            campo.value = "";
            campo.removeAttribute("id");
        });
        novaLinha.querySelector(".remover-nota").hidden = false;
        linhasNotas.appendChild(novaLinha);
    });

    linhasNotas.addEventListener("click", (evento) => {
        const botaoRemover = evento.target.closest(".remover-nota");
        if (botaoRemover) {
            botaoRemover.closest(".linha-nota").remove();
        }
    });
}
