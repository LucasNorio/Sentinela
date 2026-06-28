let ambientesMapaCache = [];
let leitoresMapaCache = [];

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

function criarBadgeStatusLeitor(status) {
  if (status === "Ativo") {
    return '<span class="badge text-bg-success">Ativo</span>';
  }

  if (status === "Manutenção") {
    return '<span class="badge text-bg-warning">Manutenção</span>';
  }

  return '<span class="badge text-bg-secondary">Inativo</span>';
}

async function carregarDadosMapa() {
  ambientesMapaCache = await requisicao("/api/ambientes?status=Todos");
  leitoresMapaCache = await requisicao("/api/leitores-rfid?status=Todos");

  atualizarResumoMapa();
  renderizarMapaAmbientes();
}

function obterLeitoresDoAmbiente(idAmbiente) {
  return leitoresMapaCache.filter((leitor) => leitor.id_ambiente === idAmbiente);
}

function atualizarResumoMapa() {
  const totalAmbientes = ambientesMapaCache.length;

  const ambientesAtivos = ambientesMapaCache.filter(
    (ambiente) => ambiente.status === "Ativo",
  ).length;

  const leitoresAtivos = leitoresMapaCache.filter(
    (leitor) => leitor.status === "Ativo",
  ).length;

  const ambientesSemLeitor = ambientesMapaCache.filter((ambiente) => {
    return obterLeitoresDoAmbiente(ambiente.id).length === 0;
  }).length;

  document.querySelector("#mapaTotalAmbientes").textContent = totalAmbientes;
  document.querySelector("#mapaAmbientesAtivos").textContent = ambientesAtivos;
  document.querySelector("#mapaLeitoresAtivos").textContent = leitoresAtivos;
  document.querySelector("#mapaAmbientesSemLeitor").textContent =
    ambientesSemLeitor;
}

function obterTextoSituacaoAmbiente(ambiente, leitores) {
  if (ambiente.status === "Inativo") {
    return "Ambiente fora de uso.";
  }

  if (ambiente.status === "Manutenção") {
    return "Ambiente temporariamente indisponível.";
  }

  if (leitores.length === 0) {
    return "Ambiente ativo, mas sem leitor RFID cadastrado.";
  }

  const leitoresAtivos = leitores.filter((leitor) => leitor.status === "Ativo");

  if (leitoresAtivos.length === 0) {
    return "Ambiente possui leitores, mas nenhum está ativo.";
  }

  return "Ambiente monitorado por RFID.";
}

function renderizarLeitoresDoAmbiente(leitores) {
  if (leitores.length === 0) {
    return `
      <span class="text-secondary">
        Nenhum leitor cadastrado
      </span>
    `;
  }

  return leitores
    .map((leitor) => {
      return `
        <div class="map-reader-item">
          <strong>${leitor.nome}</strong>
          <span>${leitor.codigo_identificacao}</span>
          <div>
            ${criarBadgeStatusLeitor(leitor.status)}
          </div>
        </div>
      `;
    })
    .join("");
}

function renderizarMapaAmbientes() {
  const tabela = document.querySelector("#tabelaMapaAmbientes");
  const contador = document.querySelector("#contadorMapaAmbientes");
  const busca = document.querySelector("#buscaMapa").value.trim().toLowerCase();
  const filtroStatus = document.querySelector("#filtroStatusMapa").value;

  let ambientes = [...ambientesMapaCache];

  if (filtroStatus !== "Todos" && filtroStatus !== "Sem leitor") {
    ambientes = ambientes.filter((ambiente) => ambiente.status === filtroStatus);
  }

  if (filtroStatus === "Sem leitor") {
    ambientes = ambientes.filter((ambiente) => {
      return obterLeitoresDoAmbiente(ambiente.id).length === 0;
    });
  }

  if (busca) {
    ambientes = ambientes.filter((ambiente) => {
      const leitores = obterLeitoresDoAmbiente(ambiente.id);

      const textoLeitores = leitores
        .map((leitor) => {
          return `${leitor.nome} ${leitor.codigo_identificacao} ${leitor.tipo_leitor} ${leitor.status}`;
        })
        .join(" ")
        .toLowerCase();

      return (
        ambiente.nome.toLowerCase().includes(busca) ||
        ambiente.bloco.toLowerCase().includes(busca) ||
        ambiente.tipo.toLowerCase().includes(busca) ||
        ambiente.status.toLowerCase().includes(busca) ||
        textoLeitores.includes(busca)
      );
    });
  }

  contador.textContent = `${ambientes.length} ambiente${
    ambientes.length === 1 ? "" : "s"
  }`;

  if (ambientes.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-secondary py-4">
          Nenhum ambiente encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = ambientes
    .map((ambiente) => {
      const leitores = obterLeitoresDoAmbiente(ambiente.id);
      const situacao = obterTextoSituacaoAmbiente(ambiente, leitores);

      return `
        <tr>
          <td>
            <strong>${ambiente.nome}</strong>
            <span>${ambiente.bloco}</span>
          </td>

          <td>${ambiente.tipo}</td>

          <td>${criarBadgeStatusAmbiente(ambiente.status)}</td>

          <td>
            <div class="map-reader-list">
              ${renderizarLeitoresDoAmbiente(leitores)}
            </div>
          </td>

          <td>${situacao}</td>
        </tr>
      `;
    })
    .join("");
}

async function iniciarMapa() {
  const buscaMapa = document.querySelector("#buscaMapa");
  const filtroStatusMapa = document.querySelector("#filtroStatusMapa");
  const btnAtualizarMapa = document.querySelector("#btnAtualizarMapa");

  buscaMapa.addEventListener("input", renderizarMapaAmbientes);
  filtroStatusMapa.addEventListener("change", renderizarMapaAmbientes);

  btnAtualizarMapa.addEventListener("click", async () => {
    try {
      await carregarDadosMapa();
    } catch (erro) {
      alert(erro.message);
    }
  });

  try {
    await carregarDadosMapa();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarMapa();
});