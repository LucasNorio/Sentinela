let leitoresCache = [];
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

function criarBadgeStatusLeitor(status) {
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
  preencherSelectAmbientes();
}

async function carregarLeitores() {
  leitoresCache = await requisicao("/api/leitores-rfid?status=Todos");
  renderizarLeitores();
}

function preencherSelectAmbientes() {
  const select = document.querySelector("#ambienteLeitor");
  const ambientesAtivos = ambientesCache.filter(
    (ambiente) => ambiente.status === "Ativo",
  );

  if (ambientesAtivos.length === 0) {
    select.innerHTML = '<option value="">Nenhum ambiente ativo cadastrado</option>';
    return;
  }

  select.innerHTML = `
    <option value="">Selecione um ambiente</option>
    ${ambientesAtivos
      .map((ambiente) => {
        return `
          <option value="${ambiente.id}">
            ${ambiente.nome} - ${ambiente.bloco}
          </option>
        `;
      })
      .join("")}
  `;
}

function limparFormularioLeitor() {
  document.querySelector("#leitorId").value = "";
  document.querySelector("#nomeLeitor").value = "";
  document.querySelector("#codigoLeitor").value = "";
  document.querySelector("#ambienteLeitor").value = "";
  document.querySelector("#tipoLeitor").value = "Interno";
  document.querySelector("#statusLeitor").value = "Ativo";
}

function preencherFormularioLeitor(id) {
  const leitor = leitoresCache.find((item) => item.id === id);

  if (!leitor) {
    return;
  }

  const selectAmbiente = document.querySelector("#ambienteLeitor");

  const ambienteExisteNoSelect = [...selectAmbiente.options].some(
    (option) => option.value === String(leitor.id_ambiente),
  );

  if (!ambienteExisteNoSelect) {
    const option = document.createElement("option");
    option.value = leitor.id_ambiente;
    option.textContent = `${leitor.ambiente} - ${leitor.bloco}`;
    selectAmbiente.appendChild(option);
  }

  document.querySelector("#leitorId").value = leitor.id;
  document.querySelector("#nomeLeitor").value = leitor.nome;
  document.querySelector("#codigoLeitor").value = leitor.codigo_identificacao;
  document.querySelector("#ambienteLeitor").value = leitor.id_ambiente;
  document.querySelector("#tipoLeitor").value = leitor.tipo_leitor;
  document.querySelector("#statusLeitor").value = leitor.status;

  document.querySelector("#formLeitor").scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

function renderizarLeitores() {
  const tabela = document.querySelector("#tabelaLeitores");
  const contador = document.querySelector("#contadorLeitores");
  const busca = document.querySelector("#buscaLeitor").value.trim().toLowerCase();
  const filtroStatus = document.querySelector("#filtroStatusLeitor").value;

  let leitores = [...leitoresCache];

  if (filtroStatus !== "Todos") {
    leitores = leitores.filter((leitor) => leitor.status === filtroStatus);
  }

  if (busca) {
    leitores = leitores.filter((leitor) => {
      return (
        leitor.nome.toLowerCase().includes(busca) ||
        leitor.codigo_identificacao.toLowerCase().includes(busca) ||
        leitor.ambiente.toLowerCase().includes(busca) ||
        leitor.bloco.toLowerCase().includes(busca) ||
        leitor.tipo_leitor.toLowerCase().includes(busca) ||
        leitor.status.toLowerCase().includes(busca)
      );
    });
  }

  contador.textContent = `${leitores.length} leitor${
    leitores.length === 1 ? "" : "es"
  }`;

  if (leitores.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">
          Nenhum leitor RFID encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = leitores
    .map((leitor) => {
      const observacao =
        leitor.motivo_inativacao ||
        leitor.motivo_manutencao ||
        "Leitor cadastrado no sistema";

      return `
        <tr>
          <td>
            <strong>${leitor.nome}</strong>
            <span>${observacao}</span>
          </td>

          <td>
            <code>${leitor.codigo_identificacao}</code>
          </td>

          <td>
            ${leitor.ambiente}
            <span>${leitor.bloco}</span>
          </td>

          <td>${leitor.tipo_leitor}</td>

          <td>${criarBadgeStatusLeitor(leitor.status)}</td>

          <td>
            <div class="table-actions">
              <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioLeitor(${leitor.id})">
                Editar
              </button>

              ${
                leitor.status === "Ativo"
                  ? `
                    <button class="btn btn-outline-warning btn-sm" onclick="colocarLeitorEmManutencao(${leitor.id})">
                      Manutenção
                    </button>

                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarLeitor(${leitor.id})">
                      Inativar
                    </button>
                  `
                  : ""
              }

              ${
                leitor.status === "Manutenção"
                  ? `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarLeitor(${leitor.id})">
                      Reativar
                    </button>

                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarLeitor(${leitor.id})">
                      Inativar
                    </button>
                  `
                  : ""
              }

              ${
                leitor.status === "Inativo"
                  ? `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarLeitor(${leitor.id})">
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

async function salvarLeitorPeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#leitorId").value;
  const nome = document.querySelector("#nomeLeitor").value.trim();
  const codigoIdentificacao = document
    .querySelector("#codigoLeitor")
    .value.trim()
    .toUpperCase();
  const idAmbiente = document.querySelector("#ambienteLeitor").value;
  const tipoLeitor = document.querySelector("#tipoLeitor").value;
  const status = document.querySelector("#statusLeitor").value;

  if (!nome || !codigoIdentificacao || !idAmbiente || !tipoLeitor || !status) {
    alert("Preencha todos os campos obrigatórios antes de salvar.");
    return;
  }

  const leitor = {
    nome,
    codigo_identificacao: codigoIdentificacao,
    id_ambiente: Number(idAmbiente),
    tipo_leitor: tipoLeitor,
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/leitores-rfid/${id}`, {
        method: "PUT",
        body: JSON.stringify(leitor),
      });
    } else {
      await requisicao("/api/leitores-rfid", {
        method: "POST",
        body: JSON.stringify(leitor),
      });
    }

    limparFormularioLeitor();
    await carregarLeitores();
  } catch (erro) {
    alert(erro.message);
  }
}

async function inativarLeitor(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Leitor RFID inativado pelo sistema.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente inativar este leitor RFID?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/leitores-rfid/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarLeitores();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarLeitor(id) {
  const confirmar = confirm("Deseja realmente reativar este leitor RFID?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/leitores-rfid/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarLeitores();
  } catch (erro) {
    alert(erro.message);
  }
}

async function colocarLeitorEmManutencao(id) {
  const motivo = prompt(
    "Informe o motivo da manutenção:",
    "Leitor RFID colocado em manutenção.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm(
    "Deseja realmente colocar este leitor RFID em manutenção?",
  );

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/leitores-rfid/${id}/manutencao`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarLeitores();
  } catch (erro) {
    alert(erro.message);
  }
}

async function iniciarGestaoLeitores() {
  const formLeitor = document.querySelector("#formLeitor");
  const buscaLeitor = document.querySelector("#buscaLeitor");
  const filtroStatusLeitor = document.querySelector("#filtroStatusLeitor");
  const btnLimparLeitor = document.querySelector("#btnLimparLeitor");
  const codigoLeitor = document.querySelector("#codigoLeitor");

  formLeitor.addEventListener("submit", salvarLeitorPeloFormulario);

  buscaLeitor.addEventListener("input", renderizarLeitores);

  filtroStatusLeitor.addEventListener("change", renderizarLeitores);

  btnLimparLeitor.addEventListener("click", () => {
    limparFormularioLeitor();
  });

  codigoLeitor.addEventListener("input", () => {
    codigoLeitor.value = codigoLeitor.value
      .toUpperCase()
      .replace(/[^A-Z0-9_-]/g, "");
  });

  try {
    await carregarAmbientes();
    await carregarLeitores();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarGestaoLeitores();
});