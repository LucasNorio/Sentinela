const formRelatorio = document.querySelector("#formRelatorio");
const selectTurma = document.querySelector("#turmaRelatorio");
const campoInicio = document.querySelector("#inicioRelatorio");
const campoFim = document.querySelector("#fimRelatorio");
const mensagem = document.querySelector("#mensagemRelatorio");
const secaoResultado = document.querySelector("#secaoResultado");
const tabelaResultado = document.querySelector("#tabelaRelatorio");
const resumoRelatorio = document.querySelector("#resumoRelatorio");
const avisoCobertura = document.querySelector("#avisoCobertura");
const btnVisualizar = document.querySelector("#btnVisualizarPdf");
const btnBaixar = document.querySelector("#btnBaixarPdf");

let consultaValidada = null;

function atualizarMensagem(texto, tipo = "secondary") {
  mensagem.className = `alert alert-${tipo} mt-3 mb-0`;
  mensagem.textContent = texto;
}

function invalidarConsulta() {
  consultaValidada = null;
  btnVisualizar.disabled = true;
  btnBaixar.disabled = true;
  secaoResultado.hidden = true;
}

function parametrosFormulario() {
  const id = selectTurma.value;
  const inicio = campoInicio.value;
  const fim = campoFim.value;
  if (!id || !inicio || !fim) {
    throw new Error("Selecione a turma e as duas datas.");
  }
  if (inicio > fim) {
    throw new Error("A data inicial não pode ser posterior à final.");
  }
  return { id, inicio, fim };
}

function caminhoRelatorio({ id, inicio, fim }, pdf = false, download = false) {
  const caminho = `/api/relatorios/turmas/${encodeURIComponent(id)}/frequencia${pdf ? ".pdf" : ""}`;
  const qs = new URLSearchParams({ inicio, fim });
  if (download) qs.set("download", "1");
  return `${caminho}?${qs}`;
}

async function solicitarDados(url) {
  const resposta = await fetch(url, { credentials: "same-origin" });
  const tipo = resposta.headers.get("content-type") || "";
  const dados = tipo.includes("application/json") ? await resposta.json() : {};
  if (!resposta.ok) throw new Error(dados.erro || `Erro ${resposta.status} na consulta.`);
  return dados;
}

function preencherTabela(dados) {
  tabelaResultado.replaceChildren();
  for (const aluno of dados.alunos) {
    const linha = document.createElement("tr");
    const percentual = aluno.frequencia_percentual === null
      ? "N/D"
      : `${aluno.frequencia_percentual.toFixed(2).replace(".", ",")}%`;
    const cobertura = `${aluno.aulas_com_registro}/${dados.aulas_finalizadas}`;
    if (aluno.cobertura_parcial) linha.classList.add("table-warning");
    for (const valor of [
      aluno.matricula, aluno.nome, aluno.presentes, aluno.atrasados,
      aluno.ausentes, aluno.justificados, cobertura, percentual,
      aluno.cobertura_parcial ? "Conferir" : "Completa",
    ]) {
      const td = document.createElement("td");
      td.textContent = String(valor);
      linha.appendChild(td);
    }
    tabelaResultado.appendChild(linha);
  }

  resumoRelatorio.textContent = `${dados.aulas_finalizadas} aulas · ${dados.total_alunos} alunos`;
  avisoCobertura.hidden = dados.alunos_cobertura_parcial === 0;
  if (dados.alunos_cobertura_parcial) {
    avisoCobertura.textContent =
      `${dados.alunos_cobertura_parcial} aluno(s) possuem registros incompletos. ` +
      "A frequência desses alunos aparece como N/D, pois não é possível determinar se houve falta ou ausência de matrícula. " +
      "O PDF será identificado como 'Para conferência' até que os registros sejam verificados.";
  }
  secaoResultado.hidden = false;
}

async function carregarTurmas() {
  try {
    const dados = await solicitarDados("/api/relatorios/turmas");
    selectTurma.replaceChildren();
    const inicial = document.createElement("option");
    inicial.value = "";
    inicial.textContent = "Selecione uma turma";
    selectTurma.appendChild(inicial);

    for (const turma of dados.turmas) {
      const opt = document.createElement("option");
      opt.value = turma.id;
      opt.textContent = `${turma.curso} · ${turma.nome} (${turma.ano_letivo})`;
      selectTurma.appendChild(opt);
    }
    turmaIndividual.replaceChildren();
    turmaIndividual.appendChild(new Option("Selecione uma turma", ""));
    for (const turma of dados.turmas) {
      turmaIndividual.appendChild(new Option(`${turma.curso} · ${turma.nome} (${turma.ano_letivo})`, turma.id));
    }
    if (!dados.turmas.length) atualizarMensagem("Não há turmas disponíveis para seu perfil.", "warning");
  } catch (erro) {
    atualizarMensagem(erro.message, "danger");
    selectTurma.replaceChildren();
    turmaIndividual.replaceChildren();
  }
}

formRelatorio.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  invalidarConsulta();
  try {
    const consulta = parametrosFormulario();
    atualizarMensagem("Consultando presenças...", "secondary");
    const dados = await solicitarDados(caminhoRelatorio(consulta));
    preencherTabela(dados);
    consultaValidada = consulta;
    btnVisualizar.disabled = false;
    btnBaixar.disabled = false;
    atualizarMensagem("Consulta concluída. Você pode visualizar ou baixar o PDF.", "success");
  } catch (erro) {
    atualizarMensagem(erro.message, "danger");
  }
});

for (const campo of [selectTurma, campoInicio, campoFim]) {
  campo.addEventListener("change", invalidarConsulta);
}

btnVisualizar.addEventListener("click", () => {
  if (consultaValidada) window.open(caminhoRelatorio(consultaValidada, true), "_blank", "noopener");
});

btnBaixar.addEventListener("click", () => {
  if (consultaValidada) window.location.assign(caminhoRelatorio(consultaValidada, true, true));
});

const agora = new Date();
const dataLocal = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000);
const anoMesDia = dataLocal.toISOString().slice(0, 10);
campoFim.value = anoMesDia;
campoInicio.value = `${anoMesDia.slice(0, 7)}-01`;
carregarTurmas();


const formIndividual = document.querySelector("#formRelatorioIndividual");
const turmaIndividual = document.querySelector("#turmaIndividual");
const alunoIndividual = document.querySelector("#alunoIndividual");
const inicioIndividual = document.querySelector("#inicioIndividual");
const fimIndividual = document.querySelector("#fimIndividual");
const mensagemIndividual = document.querySelector("#mensagemIndividual");
const secaoIndividual = document.querySelector("#secaoIndividual");
const tabelaIndividual = document.querySelector("#tabelaIndividual");
const resumoIndividual = document.querySelector("#resumoIndividual");
const avisoIndividual = document.querySelector("#avisoIndividual");
const btnVerIndividual = document.querySelector("#btnVisualizarIndividual");
const btnBaixarIndividual = document.querySelector("#btnBaixarIndividual");

let consultaIndividualValidada = null;
let buscaAlunosId = 0;
let consultaIndividualId = 0;

function atualizarMensagemIndividual(texto, tipo = "secondary") {
  mensagemIndividual.className = `alert alert-${tipo} mt-3 mb-0`;
  mensagemIndividual.textContent = texto;
}

function invalidarIndividual() {
  ++consultaIndividualId;
  consultaIndividualValidada = null;
  btnVerIndividual.disabled = true;
  btnBaixarIndividual.disabled = true;
  secaoIndividual.hidden = true;
}

async function carregarAlunosIndividual() {
  const identificador = ++buscaAlunosId;
  invalidarIndividual();
  alunoIndividual.disabled = true;
  alunoIndividual.replaceChildren();
  alunoIndividual.appendChild(new Option("Selecione um aluno", ""));
  if (!turmaIndividual.value) {
    atualizarMensagemIndividual("Selecione uma turma para carregar os alunos.");
    return;
  }
  try {
    atualizarMensagemIndividual("Carregando alunos...");
    const dados = await solicitarDados(`/api/relatorios/turmas/${encodeURIComponent(turmaIndividual.value)}/alunos`);
    if (identificador !== buscaAlunosId) return;
    for (const aluno of dados.alunos) {
      alunoIndividual.appendChild(new Option(`${aluno.matricula} · ${aluno.nome}`, aluno.id));
    }
    alunoIndividual.disabled = dados.alunos.length === 0;
    atualizarMensagemIndividual(
      dados.alunos.length ? "Selecione o aluno e o período." : "Esta turma não possui alunos disponíveis para relatório.",
      dados.alunos.length ? "secondary" : "warning"
    );
  } catch (erro) {
    if (identificador !== buscaAlunosId) return;
    atualizarMensagemIndividual(erro.message, "danger");
  }
}

function parametrosIndividual() {
  const idTurma = turmaIndividual.value;
  const idAluno = alunoIndividual.value;
  const inicio = inicioIndividual.value;
  const fim = fimIndividual.value;
  if (!idTurma || !idAluno || !inicio || !fim) {
    throw new Error("Selecione a turma, o aluno e as duas datas.");
  }
  if (inicio > fim) throw new Error("A data inicial não pode ser posterior à final.");
  return { idTurma, idAluno, inicio, fim };
}

function caminhoIndividual({ idTurma, idAluno, inicio, fim }, pdf = false, download = false) {
  const base = `/api/relatorios/turmas/${encodeURIComponent(idTurma)}/alunos/${encodeURIComponent(idAluno)}/frequencia`;
  const parametros = new URLSearchParams({ inicio, fim });
  if (download) parametros.set("download", "1");
  return `${base}${pdf ? ".pdf" : ""}?${parametros}`;
}

function preencherIndividual(dados) {
  tabelaIndividual.replaceChildren();
  const resumo = dados.resumo;
  const percentual = resumo.frequencia_percentual === null
    ? "N/D"
    : `${resumo.frequencia_percentual.toFixed(2).replace(".", ",")}%`;
  resumoIndividual.textContent = `${dados.aluno.nome} · ${resumo.aulas_com_registro}/${dados.aulas_finalizadas} registros · ${percentual}`;
  avisoIndividual.hidden = !resumo.cobertura_parcial;
  if (resumo.cobertura_parcial) {
    avisoIndividual.textContent =
      `${resumo.registros_faltantes} aula(s) sem registro de presença. ` +
      "A frequência é inconclusiva e o PDF será identificado como 'Para conferência'.";
  }
  for (const aula of dados.aulas) {
    const linha = document.createElement("tr");
    if (aula.status === "Sem registro") linha.classList.add("table-warning");
    const data = aula.data.split("-").reverse().join("/");
    for (const valor of [
      data, `#${aula.id_aula}`, `${aula.horario_inicio}–${aula.horario_fim}`,
      aula.ambiente, aula.status, aula.origem || "—",
    ]) {
      const td = document.createElement("td");
      td.textContent = String(valor);
      linha.appendChild(td);
    }
    tabelaIndividual.appendChild(linha);
  }
  secaoIndividual.hidden = false;
}

turmaIndividual.addEventListener("change", carregarAlunosIndividual);
for (const campo of [alunoIndividual, inicioIndividual, fimIndividual]) {
  campo.addEventListener("change", invalidarIndividual);
}

formIndividual.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  invalidarIndividual();
  try {
    const consulta = parametrosIndividual();
    const identificador = consultaIndividualId;
    atualizarMensagemIndividual("Consultando histórico individual...");
    const dados = await solicitarDados(caminhoIndividual(consulta));
    if (identificador !== consultaIndividualId) return;
    preencherIndividual(dados);
    consultaIndividualValidada = consulta;
    btnVerIndividual.disabled = false;
    btnBaixarIndividual.disabled = false;
    atualizarMensagemIndividual("Consulta concluída. Você pode visualizar ou baixar o PDF.", "success");
  } catch (erro) {
    atualizarMensagemIndividual(erro.message, "danger");
  }
});

btnVerIndividual.addEventListener("click", () => {
  if (consultaIndividualValidada) {
    window.open(caminhoIndividual(consultaIndividualValidada, true), "_blank", "noopener");
  }
});

btnBaixarIndividual.addEventListener("click", () => {
  if (consultaIndividualValidada) {
    window.location.assign(caminhoIndividual(consultaIndividualValidada, true, true));
  }
});

inicioIndividual.value = campoInicio.value;
fimIndividual.value = campoFim.value;
