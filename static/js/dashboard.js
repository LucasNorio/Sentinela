let resumoDashboardCache = null;

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

function textoSeguro(valor, fallback = "Não informado") {
  if (valor === null || valor === undefined || valor === "") {
    return fallback;
  }

  return valor;
}

function formatarDataHora(valor) {
  if (!valor) {
    return "Não informado";
  }

  const data = new Date(valor.replace(" ", "T"));

  if (Number.isNaN(data.getTime())) {
    return valor;
  }

  return data.toLocaleString("pt-BR");
}

function criarBadgeTipoRegistro(tipo) {
  if (tipo === "Entrada") {
    return '<span class="badge text-bg-success">Entrada</span>';
  }

  if (tipo === "Saída") {
    return '<span class="badge text-bg-primary">Saída</span>';
  }

  if (tipo === "Alerta") {
    return '<span class="badge text-bg-danger">Alerta</span>';
  }

  return '<span class="badge text-bg-secondary">Movimentação</span>';
}

async function carregarResumoDashboard() {
  resumoDashboardCache = await requisicao("/api/dashboard/resumo");
  atualizarCardsDashboard();
  renderizarUltimosRegistros();
}

function atualizarCardsDashboard() {
  document.querySelector("#homeAlunosAtivos").textContent =
    resumoDashboardCache.alunos_ativos;

  document.querySelector("#homeAlunosCadastrados").textContent =
    `${resumoDashboardCache.alunos_cadastrados} cadastrado${
      resumoDashboardCache.alunos_cadastrados === 1 ? "" : "s"
    }`;

  document.querySelector("#homeRegistrosHoje").textContent =
    resumoDashboardCache.registros_hoje;

  document.querySelector("#homeAmbientesAtivos").textContent =
    resumoDashboardCache.ambientes_ativos;

  document.querySelector("#homeAlertasHoje").textContent =
    resumoDashboardCache.alertas_hoje;

  document.querySelector("#homeProfessoresAtivos").textContent =
    resumoDashboardCache.professores_ativos;

  document.querySelector("#homeTurmasAtivas").textContent =
    resumoDashboardCache.turmas_ativas;

  document.querySelector("#homeLeitoresAtivos").textContent =
    resumoDashboardCache.leitores_ativos;

  document.querySelector("#homeLeitoresManutencao").textContent =
    resumoDashboardCache.leitores_manutencao;
}

function renderizarUltimosRegistros() {
  const tabela = document.querySelector("#homeUltimosRegistros");
  const registros = resumoDashboardCache.ultimos_registros || [];

  if (registros.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-secondary py-4">
          Nenhum registro RFID encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = registros
    .map((registro) => {
      return `
        <tr>
          <td>
            <strong>${formatarDataHora(registro.data_hora)}</strong>
            <span>ID #${registro.id}</span>
          </td>

          <td>
            <strong>${textoSeguro(registro.aluno, "Aluno não identificado")}</strong>
            <span>${textoSeguro(registro.codigo_tag_lida, "")}</span>
          </td>

          <td>
            ${textoSeguro(registro.ambiente)}
            <span>${textoSeguro(registro.bloco, "")}</span>
          </td>

          <td>
            ${textoSeguro(registro.leitor)}
            <span>${textoSeguro(registro.codigo_leitor, "")}</span>
          </td>

          <td>
            ${criarBadgeTipoRegistro(registro.tipo)}
          </td>
        </tr>
      `;
    })
    .join("");
}

async function iniciarDashboard() {
  const btnAtualizarDashboard = document.querySelector("#btnAtualizarDashboard");

  btnAtualizarDashboard.addEventListener("click", async () => {
    try {
      await carregarResumoDashboard();
    } catch (erro) {
      alert(erro.message);
    }
  });

  try {
    await carregarResumoDashboard();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarDashboard();
});