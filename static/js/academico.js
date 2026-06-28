let cursosCache = [];
let turmasCache = [];
let professoresCache = [];
let vinculosCache = [];

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

function criarBadgeStatusCurso(status) {
  if (status === "Ativo") {
    return '<span class="badge text-bg-success">Ativo</span>';
  }

  return '<span class="badge text-bg-secondary">Inativo</span>';
}

function criarBadgeStatusTurma(status) {
  if (status === "Ativa") {
    return '<span class="badge text-bg-success">Ativa</span>';
  }

  if (status === "Encerrada") {
    return '<span class="badge text-bg-warning">Encerrada</span>';
  }

  return '<span class="badge text-bg-secondary">Inativa</span>';
}

function criarBadgeStatusVinculo(status) {
  if (status === "Ativo") {
    return '<span class="badge text-bg-success">Ativo</span>';
  }

  return '<span class="badge text-bg-secondary">Inativo</span>';
}

async function carregarCursos() {
  cursosCache = await requisicao("/api/cursos?status=Todos");
  preencherSelectCursos();
  renderizarCursos();
}

async function carregarTurmas() {
  turmasCache = await requisicao("/api/turmas?status=Todos");
  preencherSelectTurmasVinculo();
  renderizarTurmas();
}

async function carregarProfessores() {
  professoresCache = await requisicao("/api/professores");
  preencherSelectProfessores();
}

async function carregarVinculos() {
  vinculosCache = await requisicao("/api/professor-turma?status=Todos");
  renderizarVinculos();
}

function preencherSelectCursos() {
  const select = document.querySelector("#cursoTurma");
  const cursosAtivos = cursosCache.filter((curso) => curso.status === "Ativo");

  if (cursosAtivos.length === 0) {
    select.innerHTML = '<option value="">Nenhum curso ativo cadastrado</option>';
    return;
  }

  select.innerHTML = `
    <option value="">Selecione um curso</option>
    ${cursosAtivos
      .map((curso) => {
        return `
          <option value="${curso.id}">
            ${curso.nome} (${curso.codigo})
          </option>
        `;
      })
      .join("")}
  `;
}

function preencherSelectProfessores() {
  const select = document.querySelector("#professorVinculo");
  const professoresAtivos = professoresCache.filter(
    (professor) => professor.status === "Ativo",
  );

  if (professoresAtivos.length === 0) {
    select.innerHTML =
      '<option value="">Nenhum professor ativo cadastrado</option>';
    return;
  }

  select.innerHTML = `
    <option value="">Selecione um professor</option>
    ${professoresAtivos
      .map((professor) => {
        return `
          <option value="${professor.id}">
            ${professor.nome} - ${professor.registro_professor}
          </option>
        `;
      })
      .join("")}
  `;
}

function preencherSelectTurmasVinculo() {
  const select = document.querySelector("#turmaVinculo");
  const turmasAtivas = turmasCache.filter((turma) => turma.status === "Ativa");

  if (turmasAtivas.length === 0) {
    select.innerHTML = '<option value="">Nenhuma turma ativa cadastrada</option>';
    return;
  }

  select.innerHTML = `
    <option value="">Selecione uma turma</option>
    ${turmasAtivas
      .map((turma) => {
        return `
          <option value="${turma.id}">
            ${turma.nome} - ${turma.curso}
          </option>
        `;
      })
      .join("")}
  `;
}

function limparFormularioCurso() {
  document.querySelector("#cursoId").value = "";
  document.querySelector("#nomeCurso").value = "";
  document.querySelector("#codigoCurso").value = "";
  document.querySelector("#statusCurso").value = "Ativo";
}

function limparFormularioTurma() {
  document.querySelector("#turmaId").value = "";
  document.querySelector("#nomeTurma").value = "";
  document.querySelector("#cursoTurma").value = "";
  document.querySelector("#periodoTurma").value = "";
  document.querySelector("#anoLetivoTurma").value = "";
  document.querySelector("#semestreTurma").value = "";
  document.querySelector("#statusTurma").value = "Ativa";
}

function limparFormularioVinculo() {
  document.querySelector("#professorTurmaId").value = "";
  document.querySelector("#professorVinculo").value = "";
  document.querySelector("#turmaVinculo").value = "";
  document.querySelector("#funcaoVinculo").value = "Professor";
  document.querySelector("#statusVinculo").value = "Ativo";
}

function preencherFormularioCurso(id) {
  const curso = cursosCache.find((item) => item.id === id);

  if (!curso) {
    return;
  }

  document.querySelector("#cursoId").value = curso.id;
  document.querySelector("#nomeCurso").value = curso.nome;
  document.querySelector("#codigoCurso").value = curso.codigo;
  document.querySelector("#statusCurso").value = curso.status;

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

function preencherFormularioTurma(id) {
  const turma = turmasCache.find((item) => item.id === id);

  if (!turma) {
    return;
  }

  const select = document.querySelector("#cursoTurma");
  const cursoExisteNoSelect = [...select.options].some(
    (option) => option.value === String(turma.id_curso),
  );

  if (!cursoExisteNoSelect) {
    const option = document.createElement("option");
    option.value = turma.id_curso;
    option.textContent = `${turma.curso} (${turma.codigo_curso})`;
    select.appendChild(option);
  }

  document.querySelector("#turmaId").value = turma.id;
  document.querySelector("#nomeTurma").value = turma.nome;
  document.querySelector("#cursoTurma").value = turma.id_curso;
  document.querySelector("#periodoTurma").value = turma.periodo;
  document.querySelector("#anoLetivoTurma").value = turma.ano_letivo;
  document.querySelector("#semestreTurma").value = turma.semestre;
  document.querySelector("#statusTurma").value = turma.status;

  document.querySelector("#formTurma").scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

function preencherFormularioVinculo(id) {
  const vinculo = vinculosCache.find((item) => item.id === id);

  if (!vinculo) {
    return;
  }

  const selectProfessor = document.querySelector("#professorVinculo");
  const professorExisteNoSelect = [...selectProfessor.options].some(
    (option) => option.value === String(vinculo.id_professor),
  );

  if (!professorExisteNoSelect) {
    const option = document.createElement("option");
    option.value = vinculo.id_professor;
    option.textContent = `${vinculo.professor} - ${vinculo.registro_professor}`;
    selectProfessor.appendChild(option);
  }

  const selectTurma = document.querySelector("#turmaVinculo");
  const turmaExisteNoSelect = [...selectTurma.options].some(
    (option) => option.value === String(vinculo.id_turma),
  );

  if (!turmaExisteNoSelect) {
    const option = document.createElement("option");
    option.value = vinculo.id_turma;
    option.textContent = `${vinculo.turma} - ${vinculo.curso}`;
    selectTurma.appendChild(option);
  }

  document.querySelector("#professorTurmaId").value = vinculo.id;
  document.querySelector("#professorVinculo").value = vinculo.id_professor;
  document.querySelector("#turmaVinculo").value = vinculo.id_turma;
  document.querySelector("#funcaoVinculo").value = vinculo.funcao;
  document.querySelector("#statusVinculo").value = vinculo.status;

  document.querySelector("#formProfessorTurma").scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

function renderizarCursos() {
  const tabela = document.querySelector("#tabelaCursos");
  const contador = document.querySelector("#contadorCursos");
  const busca = document.querySelector("#buscaCurso").value.trim().toLowerCase();
  const filtroStatus = document.querySelector("#filtroStatusCurso").value;

  let cursos = [...cursosCache];

  if (filtroStatus !== "Todos") {
    cursos = cursos.filter((curso) => curso.status === filtroStatus);
  }

  if (busca) {
    cursos = cursos.filter((curso) => {
      return (
        curso.nome.toLowerCase().includes(busca) ||
        curso.codigo.toLowerCase().includes(busca)
      );
    });
  }

  contador.textContent = `${cursos.length} curso${cursos.length === 1 ? "" : "s"}`;

  if (cursos.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="4" class="text-center text-secondary py-4">
          Nenhum curso encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = cursos
    .map((curso) => {
      return `
        <tr>
          <td>
            <strong>${curso.nome}</strong>
            <span>${curso.motivo_inativacao || "Curso cadastrado no sistema"}</span>
          </td>
          <td><code>${curso.codigo}</code></td>
          <td>${criarBadgeStatusCurso(curso.status)}</td>
          <td>
            <div class="table-actions">
              <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioCurso(${curso.id})">
                Editar
              </button>

              ${
                curso.status === "Ativo"
                  ? `
                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarCurso(${curso.id})">
                      Inativar
                    </button>
                  `
                  : `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarCurso(${curso.id})">
                      Reativar
                    </button>
                  `
              }
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderizarTurmas() {
  const tabela = document.querySelector("#tabelaTurmas");
  const contador = document.querySelector("#contadorTurmas");
  const busca = document.querySelector("#buscaTurma").value.trim().toLowerCase();
  const filtroStatus = document.querySelector("#filtroStatusTurma").value;

  let turmas = [...turmasCache];

  if (filtroStatus !== "Todos") {
    turmas = turmas.filter((turma) => turma.status === filtroStatus);
  }

  if (busca) {
    turmas = turmas.filter((turma) => {
      const anoLetivo = String(turma.ano_letivo);
      const semestre = String(turma.semestre);

      return (
        turma.nome.toLowerCase().includes(busca) ||
        turma.curso.toLowerCase().includes(busca) ||
        turma.codigo_curso.toLowerCase().includes(busca) ||
        turma.periodo.toLowerCase().includes(busca) ||
        anoLetivo.includes(busca) ||
        semestre.includes(busca)
      );
    });
  }

  contador.textContent = `${turmas.length} turma${turmas.length === 1 ? "" : "s"}`;

  if (turmas.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">
          Nenhuma turma encontrada.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = turmas
    .map((turma) => {
      return `
        <tr>
          <td>
            <strong>${turma.nome}</strong>
            <span>${turma.motivo_inativacao || turma.motivo_encerramento || "Turma cadastrada no sistema"}</span>
          </td>
          <td>
            ${turma.curso}
            <span>${turma.codigo_curso}</span>
          </td>
          <td>${turma.periodo}</td>
          <td>${turma.ano_letivo} / ${turma.semestre}º semestre</td>
          <td>${criarBadgeStatusTurma(turma.status)}</td>
          <td>
            <div class="table-actions">
              <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioTurma(${turma.id})">
                Editar
              </button>

              ${
                turma.status === "Ativa"
                  ? `
                    <button class="btn btn-outline-warning btn-sm" onclick="encerrarTurma(${turma.id})">
                      Encerrar
                    </button>

                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarTurma(${turma.id})">
                      Inativar
                    </button>
                  `
                  : `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarTurma(${turma.id})">
                      Reativar
                    </button>
                  `
              }
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderizarVinculos() {
  const tabela = document.querySelector("#tabelaVinculos");
  const contador = document.querySelector("#contadorVinculos");
  const busca = document
    .querySelector("#buscaVinculo")
    .value.trim()
    .toLowerCase();
  const filtroStatus = document.querySelector("#filtroStatusVinculo").value;

  let vinculos = [...vinculosCache];

  if (filtroStatus !== "Todos") {
    vinculos = vinculos.filter((vinculo) => vinculo.status === filtroStatus);
  }

  if (busca) {
    vinculos = vinculos.filter((vinculo) => {
      return (
        vinculo.professor.toLowerCase().includes(busca) ||
        vinculo.turma.toLowerCase().includes(busca) ||
        vinculo.curso.toLowerCase().includes(busca) ||
        vinculo.codigo_curso.toLowerCase().includes(busca) ||
        vinculo.funcao.toLowerCase().includes(busca)
      );
    });
  }

  contador.textContent = `${vinculos.length} vínculo${vinculos.length === 1 ? "" : "s"}`;

  if (vinculos.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">
          Nenhum vínculo encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = vinculos
    .map((vinculo) => {
      return `
        <tr>
          <td>
            <strong>${vinculo.professor}</strong>
            <span>${vinculo.registro_professor}</span>
          </td>
          <td>
            ${vinculo.turma}
            <span>${vinculo.periodo} - ${vinculo.ano_letivo}/${vinculo.semestre}</span>
          </td>
          <td>
            ${vinculo.curso}
            <span>${vinculo.codigo_curso}</span>
          </td>
          <td>${vinculo.funcao}</td>
          <td>${criarBadgeStatusVinculo(vinculo.status)}</td>
          <td>
            <div class="table-actions">
              <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioVinculo(${vinculo.id})">
                Editar
              </button>

              ${
                vinculo.status === "Ativo"
                  ? `
                    <button class="btn btn-outline-secondary btn-sm" onclick="inativarVinculo(${vinculo.id})">
                      Inativar
                    </button>
                  `
                  : `
                    <button class="btn btn-outline-success btn-sm" onclick="reativarVinculo(${vinculo.id})">
                      Reativar
                    </button>
                  `
              }
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

async function salvarCursoPeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#cursoId").value;
  const nome = document.querySelector("#nomeCurso").value.trim();
  const codigo = document
    .querySelector("#codigoCurso")
    .value.trim()
    .toUpperCase();
  const status = document.querySelector("#statusCurso").value;

  if (!nome || !codigo || !status) {
    alert("Preencha todos os campos obrigatórios antes de salvar.");
    return;
  }

  const curso = {
    nome,
    codigo,
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/cursos/${id}`, {
        method: "PUT",
        body: JSON.stringify(curso),
      });
    } else {
      await requisicao("/api/cursos", {
        method: "POST",
        body: JSON.stringify(curso),
      });
    }

    limparFormularioCurso();
    await carregarCursos();
    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function salvarTurmaPeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#turmaId").value;
  const nome = document.querySelector("#nomeTurma").value.trim();
  const idCurso = document.querySelector("#cursoTurma").value;
  const periodo = document.querySelector("#periodoTurma").value;
  const anoLetivo = document.querySelector("#anoLetivoTurma").value;
  const semestre = document.querySelector("#semestreTurma").value;
  const status = document.querySelector("#statusTurma").value;

  if (!nome || !idCurso || !periodo || !anoLetivo || !semestre || !status) {
    alert("Preencha todos os campos obrigatórios antes de salvar.");
    return;
  }

  const turma = {
    nome,
    id_curso: Number(idCurso),
    periodo,
    ano_letivo: Number(anoLetivo),
    semestre: Number(semestre),
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/turmas/${id}`, {
        method: "PUT",
        body: JSON.stringify(turma),
      });
    } else {
      await requisicao("/api/turmas", {
        method: "POST",
        body: JSON.stringify(turma),
      });
    }

    limparFormularioTurma();
    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function salvarVinculoPeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#professorTurmaId").value;
  const idProfessor = document.querySelector("#professorVinculo").value;
  const idTurma = document.querySelector("#turmaVinculo").value;
  const funcao = document.querySelector("#funcaoVinculo").value;
  const status = document.querySelector("#statusVinculo").value;

  if (!idProfessor || !idTurma || !funcao || !status) {
    alert("Preencha todos os campos obrigatórios antes de salvar.");
    return;
  }

  const vinculo = {
    id_professor: Number(idProfessor),
    id_turma: Number(idTurma),
    funcao,
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/professor-turma/${id}`, {
        method: "PUT",
        body: JSON.stringify(vinculo),
      });
    } else {
      await requisicao("/api/professor-turma", {
        method: "POST",
        body: JSON.stringify(vinculo),
      });
    }

    limparFormularioVinculo();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function inativarCurso(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Curso inativado pelo sistema.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente inativar este curso?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/cursos/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarCursos();
    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarCurso(id) {
  const confirmar = confirm("Deseja realmente reativar este curso?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/cursos/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarCursos();
    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function inativarTurma(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Turma inativada pelo sistema.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente inativar esta turma?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/turmas/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarTurma(id) {
  const confirmar = confirm("Deseja realmente reativar esta turma?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/turmas/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function encerrarTurma(id) {
  const motivo = prompt(
    "Informe o motivo do encerramento:",
    "Turma concluiu o período letivo.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente encerrar esta turma?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/turmas/${id}/encerrar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarTurmas();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function inativarVinculo(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Vínculo inativado pelo sistema.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm("Deseja realmente inativar este vínculo?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/professor-turma/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarVinculo(id) {
  const confirmar = confirm("Deseja realmente reativar este vínculo?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/professor-turma/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function iniciarGestaoAcademica() {
  const formCurso = document.querySelector("#formCurso");
  const formTurma = document.querySelector("#formTurma");
  const formProfessorTurma = document.querySelector("#formProfessorTurma");

  const buscaCurso = document.querySelector("#buscaCurso");
  const buscaTurma = document.querySelector("#buscaTurma");
  const buscaVinculo = document.querySelector("#buscaVinculo");

  const filtroStatusCurso = document.querySelector("#filtroStatusCurso");
  const filtroStatusTurma = document.querySelector("#filtroStatusTurma");
  const filtroStatusVinculo = document.querySelector("#filtroStatusVinculo");

  const btnLimparCurso = document.querySelector("#btnLimparCurso");
  const btnLimparTurma = document.querySelector("#btnLimparTurma");
  const btnLimparVinculo = document.querySelector("#btnLimparVinculo");

  formCurso.addEventListener("submit", salvarCursoPeloFormulario);
  formTurma.addEventListener("submit", salvarTurmaPeloFormulario);
  formProfessorTurma.addEventListener("submit", salvarVinculoPeloFormulario);

  buscaCurso.addEventListener("input", renderizarCursos);
  buscaTurma.addEventListener("input", renderizarTurmas);
  buscaVinculo.addEventListener("input", renderizarVinculos);

  filtroStatusCurso.addEventListener("change", renderizarCursos);
  filtroStatusTurma.addEventListener("change", renderizarTurmas);
  filtroStatusVinculo.addEventListener("change", renderizarVinculos);

  btnLimparCurso.addEventListener("click", () => {
    limparFormularioCurso();
  });

  btnLimparTurma.addEventListener("click", () => {
    limparFormularioTurma();
  });

  btnLimparVinculo.addEventListener("click", () => {
    limparFormularioVinculo();
  });

  try {
    await carregarCursos();
    await carregarTurmas();
    await carregarProfessores();
    await carregarVinculos();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarGestaoAcademica();
});