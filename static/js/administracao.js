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

function textoStatus(valor) {
  if (!valor) {
    return "-";
  }

  return String(valor).toUpperCase();
}

function renderizarInfoSistema(statusSistema, resumo) {
  const infoSistema = document.querySelector("#infoSistema");

  infoSistema.innerHTML = `
    <div>
      <span>Sistema</span>
      <strong>${statusSistema.sistema || "Sentinela"}</strong>
    </div>

    <div>
      <span>Versão</span>
      <strong>0.1</strong>
    </div>

    <div>
      <span>Backend</span>
      <strong>${textoStatus(statusSistema.backend)}</strong>
    </div>

    <div>
      <span>Banco de dados</span>
      <strong>${textoStatus(statusSistema.banco_de_dados)}</strong>
    </div>

    <div>
      <span>Alunos cadastrados</span>
      <strong>${resumo.alunos_cadastrados}</strong>
    </div>

    <div>
      <span>Últimos registros carregados</span>
      <strong>${resumo.ultimos_registros.length}</strong>
    </div>
  `;
}

async function carregarAdministracao() {
  const statusSistema = await requisicao("/api/status");
  const resumo = await requisicao("/api/dashboard/resumo");

  document.querySelector("#adminStatusBackend").textContent = textoStatus(
    statusSistema.backend,
  );

  document.querySelector("#adminStatusBanco").textContent = textoStatus(
    statusSistema.banco_de_dados,
  );

  document.querySelector("#adminRegistrosHoje").textContent =
    resumo.registros_hoje;

  document.querySelector("#adminAlertasHoje").textContent = resumo.alertas_hoje;

  document.querySelector("#adminAlunosAtivos").textContent =
    resumo.alunos_ativos;

  document.querySelector("#adminProfessoresAtivos").textContent =
    resumo.professores_ativos;

  document.querySelector("#adminTurmasAtivas").textContent =
    resumo.turmas_ativas;

  document.querySelector("#adminAmbientesAtivos").textContent =
    resumo.ambientes_ativos;

  document.querySelector("#adminLeitoresAtivos").textContent =
    resumo.leitores_ativos;

  document.querySelector("#adminLeitoresManutencao").textContent =
    resumo.leitores_manutencao;

  renderizarInfoSistema(statusSistema, resumo);
}

async function iniciarAdministracao() {
  const btnAtualizarAdministracao = document.querySelector(
    "#btnAtualizarAdministracao",
  );

  btnAtualizarAdministracao.addEventListener("click", async () => {
    try {
      await carregarAdministracao();
    } catch (erro) {
      alert(erro.message);
    }
  });

  try {
    await carregarAdministracao();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarAdministracao();
});