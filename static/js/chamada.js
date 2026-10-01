let aulasCache = [];
let turmasCache = [];
let ambientesCache = [];
let vinculosProfessorTurmaCache = [];

let usuarioAtual = null;
let aulaSelecionadaId = null;
let chamadaAtual = null;

let modalAula = null;
let modalCorrecao = null;
let modalHistorico = null;
let modalCancelamentoAula = null;

const filtroData = document.querySelector("#filtroData");
const filtroTurma = document.querySelector("#filtroTurma");
const filtroStatus = document.querySelector("#filtroStatus");

const btnAtualizarAulas = document.querySelector("#btnAtualizarAulas");
const btnNovaAula = document.querySelector("#btnNovaAula");
const contadorAulas = document.querySelector("#contadorAulas");
const tabelaAulas = document.querySelector("#tabelaAulas");

const secaoChamada = document.querySelector("#secaoChamada");

const formAula = document.querySelector("#formAula");
const tituloModalAula = document.querySelector("#tituloModalAula");
const avisoEstadoAula = document.querySelector("#avisoEstadoAula");
const btnSalvarAula = document.querySelector("#btnSalvarAula");

const aulaId = document.querySelector("#aulaId");
const aulaTurma = document.querySelector("#aulaTurma");
const aulaProfessor = document.querySelector("#aulaProfessor");
const aulaAmbiente = document.querySelector("#aulaAmbiente");
const aulaData = document.querySelector("#aulaData");
const aulaHorarioInicio = document.querySelector("#aulaHorarioInicio");
const aulaHorarioFim = document.querySelector("#aulaHorarioFim");
const aulaTolerancia = document.querySelector("#aulaTolerancia");

const tituloAulaSelecionada = document.querySelector("#tituloAulaSelecionada");
const statusAulaSelecionada = document.querySelector("#statusAulaSelecionada");

const detalheProfessor = document.querySelector("#detalheProfessor");
const detalheAmbiente = document.querySelector("#detalheAmbiente");
const detalheHorario = document.querySelector("#detalheHorario");
const detalheTolerancia = document.querySelector("#detalheTolerancia");

const infoCancelamentoAula = document.querySelector("#infoCancelamentoAula");
const detalheCanceladaEm = document.querySelector("#detalheCanceladaEm");
const detalheMotivoCancelamento = document.querySelector(
  "#detalheMotivoCancelamento",
);

const btnGerarChamada = document.querySelector("#btnGerarChamada");
const btnIniciarAula = document.querySelector("#btnIniciarAula");
const btnProcessarChamada = document.querySelector("#btnProcessarChamada");
const btnFinalizarChamada = document.querySelector("#btnFinalizarChamada");
const btnCancelarAula = document.querySelector("#btnCancelarAula");
const btnRecarregarChamada = document.querySelector("#btnRecarregarChamada");

const resumoPendente = document.querySelector("#resumoPendente");
const resumoPresente = document.querySelector("#resumoPresente");
const resumoAtrasado = document.querySelector("#resumoAtrasado");
const resumoAusente = document.querySelector("#resumoAusente");
const resumoJustificado = document.querySelector("#resumoJustificado");

const contadorPresencas = document.querySelector("#contadorPresencas");
const tabelaPresencas = document.querySelector("#tabelaPresencas");

const formCorrecao = document.querySelector("#formCorrecao");
const correcaoPresencaId = document.querySelector("#correcaoPresencaId");
const correcaoAluno = document.querySelector("#correcaoAluno");
const correcaoStatus = document.querySelector("#correcaoStatus");
const correcaoMotivo = document.querySelector("#correcaoMotivo");

const historicoAluno = document.querySelector("#historicoAluno");
const tabelaHistorico = document.querySelector("#tabelaHistorico");

const formCancelamentoAula = document.querySelector("#formCancelamentoAula");
const motivoCancelamentoAula = document.querySelector(
  "#motivoCancelamentoAula",
);

function escaparHtml(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function requisicaoJson(url, opcoes = {}) {
  const resposta = await fetch(url, {
    ...opcoes,
    credentials: "same-origin",
    headers: {
      ...(opcoes.body ? { "Content-Type": "application/json" } : {}),
      ...(opcoes.headers || {}),
    },
  });

  const texto = await resposta.text();
  const tipoConteudo = resposta.headers.get("content-type") || "";

  let dados = {};

  if (texto && tipoConteudo.includes("application/json")) {
    try {
      dados = JSON.parse(texto);
    } catch {
      dados = {};
    }
  }

  if (!resposta.ok) {
    throw new Error(
      dados.erro || `Erro ${resposta.status} ao processar a requisição.`,
    );
  }

  return dados;
}

function formatarData(data) {
  if (!data) {
    return "-";
  }

  const partes = data.split("-");

  if (partes.length !== 3) {
    return data;
  }

  return `${partes[2]}/${partes[1]}/${partes[0]}`;
}

function formatarHorario(horario) {
  if (!horario) {
    return "-";
  }

  return horario.substring(0, 5);
}

function formatarDataHora(dataHora) {
  if (!dataHora) {
    return "-";
  }

  const valor = String(dataHora).replace("T", " ");
  const [data, horario] = valor.split(" ");

  if (!data || !horario) {
    return valor;
  }

  return `${formatarData(data)} ${horario.substring(0, 5)}`;
}

function classeBadgeAula(status) {
  if (status === "Em andamento") {
    return "text-bg-warning";
  }

  if (status === "Finalizada") {
    return "text-bg-success";
  }

  if (status === "Cancelada") {
    return "text-bg-danger";
  }

  return "text-bg-secondary";
}

function classeBadgePresenca(status) {
  if (status === "Presente") {
    return "text-bg-success";
  }

  if (status === "Atrasado") {
    return "text-bg-warning";
  }

  if (status === "Ausente") {
    return "text-bg-danger";
  }

  if (status === "Justificado") {
    return "text-bg-info";
  }

  return "text-bg-secondary";
}

function usuarioEhProfessor() {
  return usuarioAtual?.perfil === "Professor";
}

function usuarioPodeGerenciarAulas() {
  return ["Administrador", "Coordenação", "Secretaria"].includes(
    usuarioAtual?.perfil,
  );
}

function usuarioPodeCancelarAula() {
  return ["Administrador", "Coordenação"].includes(usuarioAtual?.perfil);
}

async function carregarUsuarioAtual() {
  const dados = await requisicaoJson("/api/auth/me");

  usuarioAtual = dados.usuario;

  return usuarioAtual;
}

async function carregarVinculosProfessorTurma() {
  try {
    const dados = await requisicaoJson("/api/professor-turma");

    vinculosProfessorTurmaCache = Array.isArray(dados)
      ? dados
      : dados.vinculos || [];
  } catch (erro) {
    console.error("Erro ao carregar vínculos professor-turma:", erro);
    vinculosProfessorTurmaCache = [];
  }
}

async function carregarTurmas() {
  try {
    const dados = await requisicaoJson("/api/turmas?status=Ativa");

    turmasCache = Array.isArray(dados) ? dados : dados.turmas || [];

    let turmasVisiveis = turmasCache;

    if (usuarioEhProfessor()) {
      const idsTurmasPermitidas = new Set(
        vinculosProfessorTurmaCache
          .filter(
            (vinculo) =>
              Number(vinculo.id_professor) ===
                Number(usuarioAtual.id_professor) &&
              vinculo.status === "Ativo" &&
              (vinculo.funcao === "Professor" || vinculo.funcao === "Auxiliar"),
          )
          .map((vinculo) => Number(vinculo.id_turma)),
      );

      turmasVisiveis = turmasCache.filter((turma) =>
        idsTurmasPermitidas.has(Number(turma.id)),
      );
    }

    filtroTurma.innerHTML = `
            <option value="">
                ${
                  usuarioEhProfessor()
                    ? "Todas as minhas turmas"
                    : "Todas as turmas"
                }
            </option>
        `;

    if (usuarioPodeGerenciarAulas()) {
      aulaTurma.innerHTML = `
                <option value="">Selecione a turma</option>
            `;
    }

    turmasVisiveis.forEach((turma) => {
      const id = Number(turma.id);
      const nome = escaparHtml(turma.nome);

      filtroTurma.innerHTML += `
                <option value="${id}">${nome}</option>
            `;

      if (usuarioPodeGerenciarAulas()) {
        aulaTurma.innerHTML += `
                    <option value="${id}">${nome}</option>
                `;
      }
    });
  } catch (erro) {
    console.error("Erro ao carregar turmas:", erro);
  }
}

async function carregarAmbientes() {
  try {
    const dados = await requisicaoJson("/api/ambientes");

    ambientesCache = Array.isArray(dados) ? dados : dados.ambientes || [];

    const ambientesAtivos = ambientesCache.filter(
      (ambiente) => ambiente.status === "Ativo",
    );

    aulaAmbiente.innerHTML = `
            <option value="">Selecione o ambiente</option>
        `;

    ambientesAtivos.forEach((ambiente) => {
      aulaAmbiente.innerHTML += `
                <option value="${Number(ambiente.id)}">
                    ${escaparHtml(ambiente.nome)}
                </option>
            `;
    });
  } catch (erro) {
    console.error("Erro ao carregar ambientes:", erro);
  }
}

function aplicarPermissoesChamada() {
  btnNovaAula.style.display = usuarioPodeGerenciarAulas() ? "" : "none";
}

function atualizarProfessoresPorTurma() {
  const idTurma = Number(aulaTurma.value);

  aulaProfessor.innerHTML = `
        <option value="">Selecione o professor</option>
    `;

  if (!idTurma) {
    return;
  }

  const vinculosValidos = vinculosProfessorTurmaCache.filter(
    (vinculo) =>
      Number(vinculo.id_turma) === idTurma &&
      vinculo.status === "Ativo" &&
      (vinculo.funcao === "Professor" || vinculo.funcao === "Auxiliar"),
  );

  if (!vinculosValidos.length) {
    aulaProfessor.innerHTML = `
            <option value="">Nenhum professor vinculado</option>
        `;
    return;
  }

  vinculosValidos.forEach((vinculo) => {
    aulaProfessor.innerHTML += `
            <option value="${Number(vinculo.id_professor)}">
                ${escaparHtml(vinculo.professor)} — ${escaparHtml(vinculo.funcao)}
            </option>
        `;
  });
}

function limparFormularioAula() {
  formAula.reset();

  aulaId.value = "";
  aulaTolerancia.value = "15";
  aulaProfessor.innerHTML = `
        <option value="">Selecione primeiro uma turma</option>
    `;

  tituloModalAula.textContent = "Nova aula";
  btnSalvarAula.textContent = "Salvar aula";

  avisoEstadoAula.innerHTML = `
        A nova aula será criada com status
        <strong>Programada</strong>.
    `;
}

function abrirNovaAula() {
  if (!usuarioPodeGerenciarAulas()) {
    alert("Você não possui permissão para cadastrar aulas.");
    return;
  }

  limparFormularioAula();
  modalAula.show();
}

function editarAula(idAula) {
  if (!usuarioPodeGerenciarAulas()) {
    alert("Você não possui permissão para editar aulas.");
    return;
  }

  const aula = aulasCache.find((item) => item.id === idAula);

  if (!aula) {
    return;
  }

  if (aula.status !== "Programada") {
    alert("Somente aulas programadas podem ser editadas.");
    return;
  }

  aulaId.value = aula.id;
  aulaTurma.value = aula.id_turma;

  atualizarProfessoresPorTurma();

  aulaProfessor.value = aula.id_professor;
  aulaAmbiente.value = aula.id_ambiente;
  aulaData.value = aula.data_aula;
  aulaHorarioInicio.value = formatarHorario(aula.horario_inicio);
  aulaHorarioFim.value = formatarHorario(aula.horario_fim);
  aulaTolerancia.value = aula.tolerancia_minutos;

  tituloModalAula.textContent = "Editar aula";
  btnSalvarAula.textContent = "Atualizar aula";

  avisoEstadoAula.innerHTML = `
        A edição mantém a aula com status
        <strong>Programada</strong>.
    `;

  modalAula.show();
}

async function salvarAula(event) {
  event.preventDefault();

  if (!usuarioPodeGerenciarAulas()) {
    alert("Você não possui permissão para salvar aulas.");
    return;
  }

  const id = aulaId.value;

  if (id) {
    const aula = aulasCache.find((item) => item.id === Number(id));

    if (!aula || aula.status !== "Programada") {
      alert("Somente aulas programadas podem ser editadas.");
      return;
    }
  }

  const dados = {
    id_turma: Number(aulaTurma.value),
    id_professor: Number(aulaProfessor.value),
    id_ambiente: Number(aulaAmbiente.value),
    data_aula: aulaData.value,
    horario_inicio: aulaHorarioInicio.value,
    horario_fim: aulaHorarioFim.value,
    tolerancia_minutos: Number(aulaTolerancia.value),
  };

  if (
    !dados.id_turma ||
    !dados.id_professor ||
    !dados.id_ambiente ||
    !dados.data_aula ||
    !dados.horario_inicio ||
    !dados.horario_fim
  ) {
    alert("Preencha todos os campos obrigatórios.");
    return;
  }

  if (dados.horario_fim <= dados.horario_inicio) {
    alert("O horário de fim deve ser maior que o horário de início.");
    return;
  }

  if (
    !Number.isInteger(dados.tolerancia_minutos) ||
    dados.tolerancia_minutos < 0 ||
    dados.tolerancia_minutos > 120
  ) {
    alert("A tolerância deve estar entre 0 e 120 minutos.");
    return;
  }

  try {
    const resposta = id
      ? await requisicaoJson(`/api/aulas/${id}`, {
          method: "PUT",
          body: JSON.stringify(dados),
        })
      : await requisicaoJson("/api/aulas", {
          method: "POST",
          body: JSON.stringify(dados),
        });

    modalAula.hide();

    alert(resposta.mensagem || "Aula salva com sucesso.");

    limparFormularioAula();
    await carregarAulas();
  } catch (erro) {
    alert(erro.message);
  }
}

function montarQueryAulas() {
  const parametros = new URLSearchParams();

  if (filtroData.value) {
    parametros.set("data", filtroData.value);
  }

  if (filtroTurma.value) {
    parametros.set("id_turma", filtroTurma.value);
  }

  if (filtroStatus.value) {
    parametros.set("status", filtroStatus.value);
  }

  const query = parametros.toString();

  return query ? `?${query}` : "";
}

async function carregarAulas() {
  tabelaAulas.innerHTML = `
        <tr>
            <td colspan="7" class="text-center text-muted py-4">
                Carregando aulas...
            </td>
        </tr>
    `;

  try {
    const dados = await requisicaoJson(`/api/aulas${montarQueryAulas()}`);

    aulasCache = dados.aulas || [];
    renderizarAulas();
  } catch (erro) {
    tabelaAulas.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger py-4">
                    ${escaparHtml(erro.message)}
                </td>
            </tr>
        `;
  }
}

function renderizarAulas() {
  contadorAulas.textContent = `${aulasCache.length} aula${aulasCache.length === 1 ? "" : "s"}`;

  if (!aulasCache.length) {
    tabelaAulas.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    Nenhuma aula encontrada.
                </td>
            </tr>
        `;
    return;
  }

  tabelaAulas.innerHTML = aulasCache
    .map((aula) => {
      const podeEditar =
        usuarioPodeGerenciarAulas() && aula.status === "Programada";

      return `
                <tr>
                    <td>
                        <strong>${escaparHtml(formatarData(aula.data_aula))}</strong>
                    </td>
                    <td>${escaparHtml(aula.turma)}</td>
                    <td>${escaparHtml(aula.professor)}</td>
                    <td>${escaparHtml(aula.ambiente)}</td>
                    <td>
                        ${escaparHtml(formatarHorario(aula.horario_inicio))}
                        -
                        ${escaparHtml(formatarHorario(aula.horario_fim))}
                    </td>
                    <td>
                        <span class="badge rounded-pill ${classeBadgeAula(aula.status)}">
                            ${escaparHtml(aula.status)}
                        </span>
                    </td>
                    <td>
                        <div class="table-actions">
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-danger fw-bold"
                                onclick="abrirChamada(${Number(aula.id)})"
                            >
                                Abrir
                            </button>

                            ${
                              podeEditar
                                ? `
                                    <button
                                        type="button"
                                        class="btn btn-sm btn-outline-secondary fw-bold"
                                        onclick="editarAula(${Number(aula.id)})"
                                    >
                                        Editar
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

// Substitua a função abrirChamada por esta versão:
async function abrirChamada(idAula, silencioso = false) {
  if (!silencioso) {
    tabelaPresencas.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    Carregando chamada...
                </td>
            </tr>
        `;
  }

  try {
    const dados = await requisicaoJson(`/api/chamadas/${idAula}`);

    aulaSelecionadaId = idAula;
    chamadaAtual = dados;

    secaoChamada.classList.remove("d-none");
    renderizarChamada();

    // Só faz o scroll se NÃO for uma atualização silenciosa
    if (!silencioso) {
      secaoChamada.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  } catch (erro) {
    if (!silencioso) {
      aulaSelecionadaId = null;
      chamadaAtual = null;
      secaoChamada.classList.add("d-none");
      alert(erro.message);
    }
  }
}

function renderizarChamada() {
  if (!chamadaAtual) {
    return;
  }

  const aula = chamadaAtual.aula;
  const resumo = chamadaAtual.resumo || {};

  tituloAulaSelecionada.textContent = `${aula.turma} — ${formatarData(aula.data_aula)}`;

  statusAulaSelecionada.textContent = aula.status;
  statusAulaSelecionada.className = `badge rounded-pill ${classeBadgeAula(aula.status)}`;

  detalheProfessor.textContent = aula.professor || "-";
  detalheAmbiente.textContent = aula.ambiente || "-";
  detalheHorario.textContent = `${formatarHorario(aula.horario_inicio)} - ${formatarHorario(aula.horario_fim)}`;
  detalheTolerancia.textContent = `${aula.tolerancia_minutos ?? 0} minutos`;

  if (aula.status === "Cancelada") {
    infoCancelamentoAula.classList.remove("d-none");
    detalheCanceladaEm.textContent = formatarDataHora(aula.cancelada_em);
    detalheMotivoCancelamento.textContent = aula.motivo_cancelamento || "-";
  } else {
    infoCancelamentoAula.classList.add("d-none");
    detalheCanceladaEm.textContent = "-";
    detalheMotivoCancelamento.textContent = "-";
  }

  resumoPendente.textContent = resumo.Pendente || 0;
  resumoPresente.textContent = resumo.Presente || 0;
  resumoAtrasado.textContent = resumo.Atrasado || 0;
  resumoAusente.textContent = resumo.Ausente || 0;
  resumoJustificado.textContent = resumo.Justificado || 0;

  renderizarPresencas();
  atualizarBotoesChamada();
}

function renderizarPresencas() {
  const presencas = chamadaAtual?.presencas || [];
  const aula = chamadaAtual?.aula;

  contadorPresencas.textContent = `${presencas.length} aluno${presencas.length === 1 ? "" : "s"}`;

  if (!presencas.length) {
    const mensagem =
      aula?.status === "Cancelada"
        ? "A aula foi cancelada e não possui chamada processável."
        : "A chamada ainda não foi gerada para esta aula.";

    tabelaPresencas.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    ${escaparHtml(mensagem)}
                </td>
            </tr>
        `;
    return;
  }

  tabelaPresencas.innerHTML = presencas
    .map((presenca) => {
      const alunoInativo =
        presenca.status_aluno && presenca.status_aluno !== "Ativo";

      const tagInvalida =
        presenca.status_tag && presenca.status_tag !== "Ativa";

      const podeCorrigir = aula?.status !== "Cancelada";

      return `
                <tr>
                    <td>
                        <strong>${escaparHtml(presenca.aluno)}</strong>

                        ${
                          alunoInativo
                            ? `
                                <small class="d-block text-danger mt-1">
                                    Aluno ${escaparHtml(presenca.status_aluno)}
                                </small>
                            `
                            : ""
                        }
                    </td>

                    <td>
                        ${escaparHtml(presenca.matricula || "-")}
                    </td>

                    <td>
                        ${
                          presenca.codigo_tag
                            ? `<code>${escaparHtml(presenca.codigo_tag)}</code>`
                            : "-"
                        }

                        ${
                          tagInvalida
                            ? `
                                <small class="d-block text-danger mt-1">
                                    Tag ${escaparHtml(presenca.status_tag)}
                                </small>
                            `
                            : ""
                        }
                    </td>

                    <td>
                        <span
                            class="badge rounded-pill ${classeBadgePresenca(presenca.status)}"
                        >
                            ${escaparHtml(presenca.status)}
                        </span>
                    </td>

                    <td>
                        ${escaparHtml(presenca.origem || "-")}
                    </td>

                    <td>
                        ${escaparHtml(
                          formatarDataHora(presenca.horario_detectado),
                        )}
                    </td>

                    <td>
                        <div class="table-actions">
                            ${
                              podeCorrigir
                                ? `
                                    <button
                                        type="button"
                                        class="btn btn-sm btn-outline-secondary fw-bold"
                                        onclick="abrirModalCorrecao(${Number(presenca.id)})"
                                    >
                                        Corrigir
                                    </button>
                                `
                                : ""
                            }

                            <button
                                type="button"
                                class="btn btn-sm btn-outline-secondary fw-bold"
                                onclick="abrirHistorico(${Number(presenca.id)})"
                            >
                                Histórico
                            </button>
                        </div>
                    </td>
                </tr>
            `;
    })
    .join("");
}

function atualizarBotoesChamada() {
  const aula = chamadaAtual?.aula;

  if (!aula) {
    return;
  }

  const status = aula.status;

  const chamadaGerada = (chamadaAtual?.presencas || []).length > 0;

  btnCancelarAula.style.display = usuarioPodeCancelarAula() ? "" : "none";

  if (status === "Programada") {
    btnGerarChamada.disabled = false;
    btnIniciarAula.disabled = !chamadaGerada;
    btnProcessarChamada.disabled = true;
    btnFinalizarChamada.disabled = true;

    btnCancelarAula.disabled = !usuarioPodeCancelarAula();

    return;
  }

  if (status === "Em andamento") {
    btnGerarChamada.disabled = false;
    btnIniciarAula.disabled = true;
    btnProcessarChamada.disabled = false;
    btnFinalizarChamada.disabled = false;
    btnCancelarAula.disabled = true;

    return;
  }

  btnGerarChamada.disabled = true;
  btnIniciarAula.disabled = true;
  btnProcessarChamada.disabled = true;
  btnFinalizarChamada.disabled = true;
  btnCancelarAula.disabled = true;
}

async function executarAcaoChamada(url, confirmacao = null) {
  if (!aulaSelecionadaId) {
    return;
  }

  if (confirmacao && !window.confirm(confirmacao)) {
    return;
  }

  try {
    const dados = await requisicaoJson(url, {
      method: "POST",
    });

    alert(dados.mensagem || "Operação realizada com sucesso.");

    await abrirChamada(aulaSelecionadaId);
    await carregarAulas();
  } catch (erro) {
    alert(erro.message);
  }
}

function abrirModalCorrecao(idPresenca) {
  const presenca = chamadaAtual?.presencas.find(
    (item) => item.id === idPresenca,
  );

  if (!presenca) {
    return;
  }

  if (chamadaAtual?.aula?.status === "Cancelada") {
    alert("Não é possível corrigir presença de uma aula cancelada.");

    return;
  }

  correcaoPresencaId.value = presenca.id;
  correcaoAluno.textContent = presenca.aluno;
  correcaoStatus.value = "";
  correcaoMotivo.value = "";

  modalCorrecao.show();
}

async function salvarCorrecao(event) {
  event.preventDefault();

  const idPresenca = correcaoPresencaId.value;

  const status = correcaoStatus.value;

  const motivo = correcaoMotivo.value.trim();

  if (!status) {
    alert("Selecione o novo status.");
    return;
  }

  if (!motivo) {
    alert("Informe o motivo da correção.");

    return;
  }

  try {
    const dados = await requisicaoJson(
      `/api/presencas/${idPresenca}/corrigir`,
      {
        method: "PATCH",
        body: JSON.stringify({
          status,
          motivo,
        }),
      },
    );

    modalCorrecao.hide();

    alert(dados.mensagem);

    await abrirChamada(aulaSelecionadaId);
  } catch (erro) {
    alert(erro.message);
  }
}

async function abrirHistorico(idPresenca) {
  historicoAluno.textContent = "-";

  tabelaHistorico.innerHTML = `
        <tr>
            <td
                colspan="4"
                class="text-center text-muted py-4"
            >
                Carregando histórico...
            </td>
        </tr>
    `;

  modalHistorico.show();

  try {
    const dados = await requisicaoJson(`/api/presencas/${idPresenca}/ajustes`);

    historicoAluno.textContent = dados.presenca?.aluno || "-";

    const ajustes = dados.ajustes || [];

    if (!ajustes.length) {
      tabelaHistorico.innerHTML = `
                <tr>
                    <td
                        colspan="4"
                        class="text-center text-muted py-4"
                    >
                        Nenhuma correção registrada para esta presença.
                    </td>
                </tr>
            `;

      return;
    }

    tabelaHistorico.innerHTML = ajustes
      .map(
        (ajuste) => `
                        <tr>
                            <td>
                                ${escaparHtml(
                                  formatarDataHora(ajuste.criado_em),
                                )}
                            </td>

                            <td>
                                <strong>
                                    ${escaparHtml(ajuste.status_anterior)}
                                </strong>

                                →

                                <strong>
                                    ${escaparHtml(ajuste.status_novo)}
                                </strong>
                            </td>

                            <td>
                                ${escaparHtml(ajuste.usuario)}

                                <br />

                                <small
                                    class="text-muted"
                                >
                                    ${escaparHtml(ajuste.perfil_usuario)}
                                </small>
                            </td>

                            <td>
                                ${escaparHtml(ajuste.motivo)}
                            </td>
                        </tr>
                    `,
      )
      .join("");
  } catch (erro) {
    tabelaHistorico.innerHTML = `
            <tr>
                <td
                    colspan="4"
                    class="text-center text-danger py-4"
                >
                    ${escaparHtml(erro.message)}
                </td>
            </tr>
        `;
  }
}

function abrirCancelamentoAula() {
  if (!aulaSelecionadaId) {
    return;
  }

  if (!usuarioPodeCancelarAula()) {
    alert("Você não possui permissão para cancelar aulas.");

    return;
  }

  if (chamadaAtual?.aula?.status !== "Programada") {
    alert("Somente aulas programadas podem ser canceladas.");

    return;
  }

  motivoCancelamentoAula.value = "";

  modalCancelamentoAula.show();
}

async function cancelarAula(event) {
  event.preventDefault();

  if (!aulaSelecionadaId) {
    return;
  }

  const motivo = motivoCancelamentoAula.value.trim();

  if (!motivo) {
    alert("Informe o motivo do cancelamento.");

    return;
  }

  try {
    const dados = await requisicaoJson(
      `/api/aulas/${aulaSelecionadaId}/cancelar`,
      {
        method: "PATCH",
        body: JSON.stringify({
          motivo,
        }),
      },
    );

    modalCancelamentoAula.hide();

    formCancelamentoAula.reset();

    alert(dados.mensagem);

    await abrirChamada(aulaSelecionadaId);

    await carregarAulas();
  } catch (erro) {
    alert(erro.message);
  }
}

function iniciarEventos() {
  btnAtualizarAulas.addEventListener("click", carregarAulas);

  filtroData.addEventListener("change", carregarAulas);

  filtroTurma.addEventListener("change", carregarAulas);

  filtroStatus.addEventListener("change", carregarAulas);

  btnNovaAula.addEventListener("click", abrirNovaAula);

  formAula.addEventListener("submit", salvarAula);

  aulaTurma.addEventListener("change", atualizarProfessoresPorTurma);

  btnGerarChamada.addEventListener("click", () => {
    executarAcaoChamada(`/api/chamadas/${aulaSelecionadaId}/gerar`);
  });

  btnIniciarAula.addEventListener("click", async () => {
    if (!aulaSelecionadaId) {
      return;
    }

    if (!window.confirm("Deseja iniciar esta aula?")) {
      return;
    }

    try {
      const dados = await requisicaoJson(
        `/api/aulas/${aulaSelecionadaId}/iniciar`,
        {
          method: "PATCH",
        },
      );

      alert(dados.mensagem);

      await abrirChamada(aulaSelecionadaId);

      await carregarAulas();
    } catch (erro) {
      alert(erro.message);
    }
  });

  btnProcessarChamada.addEventListener("click", () => {
    executarAcaoChamada(`/api/chamadas/${aulaSelecionadaId}/processar`);
  });

  btnFinalizarChamada.addEventListener("click", () => {
    executarAcaoChamada(
      `/api/chamadas/${aulaSelecionadaId}/finalizar`,
      "Deseja realmente finalizar esta chamada? Alunos ainda pendentes serão marcados como ausentes.",
    );
  });

  btnCancelarAula.addEventListener("click", abrirCancelamentoAula);

  formCancelamentoAula.addEventListener("submit", cancelarAula);

  btnRecarregarChamada.addEventListener("click", () => {
    if (aulaSelecionadaId) {
      abrirChamada(aulaSelecionadaId);
    }
  });

  formCorrecao.addEventListener("submit", salvarCorrecao);
}

document.addEventListener("DOMContentLoaded", async () => {
  modalAula = new bootstrap.Modal(document.querySelector("#modalAula"));

  modalCorrecao = new bootstrap.Modal(document.querySelector("#modalCorrecao"));

  modalHistorico = new bootstrap.Modal(
    document.querySelector("#modalHistorico"),
  );

  modalCancelamentoAula = new bootstrap.Modal(
    document.querySelector("#modalCancelamentoAula"),
  );

  iniciarEventos();

  try {
    await carregarUsuarioAtual();

    aplicarPermissoesChamada();

    await carregarVinculosProfessorTurma();

    await carregarTurmas();

    if (usuarioPodeGerenciarAulas()) {
      await carregarAmbientes();
    }

    await carregarAulas();

    setInterval(async () => {
      if (aulaSelecionadaId && chamadaAtual?.aula?.status === "Em andamento") {
        await abrirChamada(aulaSelecionadaId, true); // true = atualização silenciosa
      }
    }, 3000);
  } catch (erro) {
    console.error("Erro ao inicializar página de chamada:", erro);
  }
});
