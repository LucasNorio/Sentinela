let ambientesCache = [];

async function requisicao(url, opcoes = {}) {
  const resposta = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...opcoes,
  });

  const texto = await resposta.text();

  let dados = {};

  if (texto) {
    try {
      dados = JSON.parse(texto);
    } catch {
      dados = {
        erro: texto,
      };
    }
  }

  if (!resposta.ok) {
    throw new Error(
      dados.erro || `Erro ${resposta.status} ao processar a requisição.`,
    );
  }

  return dados;
}

function criarBadgeStatusAmbiente(status) {
  if (status === "Ativo") {
    return '<span class="badge text-bg-success">Ativo</span>';
  }

  if (status === "Manutenção") {
    return '<span class="badge text-bg-warning">Manutenção</span>';
  }

  return '<span class="badge text-bg-secondary">Inativo</span>';
}

async function carregarAmbientes() {
  ambientesCache = await requisicao("/api/ambientes?status=Todos");
  renderizarAmbientes();
}

function limparFormularioAmbiente() {
  document.querySelector("#ambienteId").value = "";
  document.querySelector("#nomeAmbiente").value = "";
  document.querySelector("#blocoAmbiente").value = "";
  document.querySelector("#tipoAmbiente").value = "";
  document.querySelector("#capacidadeAmbiente").value = "";
  document.querySelector("#statusAmbiente").value = "Ativo";
}

function preencherFormularioAmbiente(id) {
  const ambiente = ambientesCache.find((item) => item.id === id);

  if (!ambiente) {
    return;
  }

  document.querySelector("#ambienteId").value = ambiente.id;
  document.querySelector("#nomeAmbiente").value = ambiente.nome;
  document.querySelector("#blocoAmbiente").value = ambiente.bloco;
  document.querySelector("#tipoAmbiente").value = ambiente.tipo;
  document.querySelector("#capacidadeAmbiente").value =
    ambiente.capacidade || "";
  document.querySelector("#statusAmbiente").value = ambiente.status;

  document.querySelector("#formAmbiente").scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

function renderizarAmbientes() {
  const tabela = document.querySelector("#tabelaAmbientes");
  const contador = document.querySelector("#contadorAmbientes");
  const busca = document
    .querySelector("#buscaAmbiente")
    .value.trim()
    .toLowerCase();
  const filtroStatus = document.querySelector("#filtroStatusAmbiente").value;

  let ambientes = [...ambientesCache];

  if (filtroStatus !== "Todos") {
    ambientes = ambientes.filter(
      (ambiente) => ambiente.status === filtroStatus,
    );
  }

  if (busca) {
    ambientes = ambientes.filter((ambiente) => {
      const capacidade = ambiente.capacidade
        ? String(ambiente.capacidade)
        : "";

      return (
        ambiente.nome.toLowerCase().includes(busca) ||
        ambiente.bloco.toLowerCase().includes(busca) ||
        ambiente.tipo.toLowerCase().includes(busca) ||
        ambiente.status.toLowerCase().includes(busca) ||
        capacidade.includes(busca)
      );
    });
  }

  contador.textContent = `${ambientes.length} ambiente${
    ambientes.length === 1 ? "" : "s"
  }`;

  if (ambientes.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">
          Nenhum ambiente encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = ambientes
    .map((ambiente) => {
      const observacao =
        ambiente.motivo_inativacao ||
        ambiente.motivo_manutencao ||
        "Ambiente cadastrado no sistema";

      return `
        <tr>
          <td>
            <strong>${ambiente.nome}</strong>
            <span>${observacao}</span>
          </td>

          <td>${ambiente.bloco}</td>

          <td>${ambiente.tipo}</td>

          <td>${ambiente.capacidade || "Não informada"}</td>

          <td>${criarBadgeStatusAmbiente(ambiente.status)}</td>

          <td>
            <div class="table-actions">
              <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioAmbiente(${ambiente.id})">
                Editar
              </button>

              ${
                ambiente.status === "Ativo"
                  ? `
                    <button class="btn btn-outline-warning btn-sm" onclick="colocarAmbienteEmManutencao(${ambiente.id})">
                      Manutenção
                    </button>

                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarAmbiente(${ambiente.id})">
                      Inativar
                    </button>
                  `
                  : ""
              }

              ${
                ambiente.status === "Manutenção"
                  ? `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarAmbiente(${ambiente.id})">
                      Reativar
                    </button>

                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarAmbiente(${ambiente.id})">
                      Inativar
                    </button>
                  `
                  : ""
              }

              ${
                ambiente.status === "Inativo"
                  ? `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarAmbiente(${ambiente.id})">
                      Reativar
                    </button>
                  `
                  : ""
              }
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

async function salvarAmbientePeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#ambienteId").value;
  const nome = document.querySelector("#nomeAmbiente").value.trim();
  const bloco = document.querySelector("#blocoAmbiente").value.trim();
  const tipo = document.querySelector("#tipoAmbiente").value;
  const capacidade = document.querySelector("#capacidadeAmbiente").value;
  const status = document.querySelector("#statusAmbiente").value;

  if (!nome || !bloco || !tipo || !status) {
    alert("Preencha todos os campos obrigatórios antes de salvar.");
    return;
  }

  const ambiente = {
    nome,
    bloco,
    tipo,
    capacidade: capacidade ? Number(capacidade) : null,
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/ambientes/${id}`, {
        method: "PUT",
        body: JSON.stringify(ambiente),
      });
    } else {
      await requisicao("/api/ambientes", {
        method: "POST",
        body: JSON.stringify(ambiente),
      });
    }

    limparFormularioAmbiente();
    await carregarAmbientes();
  } catch (erro) {
    alert(erro.message);
  }
}

async function inativarAmbiente(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Ambiente inativado pelo sistema.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente inativar este ambiente?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/ambientes/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarAmbientes();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarAmbiente(id) {
  const confirmar = confirm("Deseja realmente reativar este ambiente?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/ambientes/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarAmbientes();
  } catch (erro) {
    alert(erro.message);
  }
}

async function colocarAmbienteEmManutencao(id) {
  const motivo = prompt(
    "Informe o motivo da manutenção:",
    "Ambiente colocado em manutenção.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente colocar este ambiente em manutenção?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/ambientes/${id}/manutencao`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarAmbientes();
  } catch (erro) {
    alert(erro.message);
  }
}

async function iniciarGestaoAmbientes() {
  const formAmbiente = document.querySelector("#formAmbiente");
  const buscaAmbiente = document.querySelector("#buscaAmbiente");
  const filtroStatusAmbiente = document.querySelector("#filtroStatusAmbiente");
  const btnLimparAmbiente = document.querySelector("#btnLimparAmbiente");

  formAmbiente.addEventListener("submit", salvarAmbientePeloFormulario);

  buscaAmbiente.addEventListener("input", renderizarAmbientes);

  filtroStatusAmbiente.addEventListener("change", renderizarAmbientes);

  btnLimparAmbiente.addEventListener("click", () => {
    limparFormularioAmbiente();
  });

  try {
    await carregarAmbientes();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarGestaoAmbientes();
});