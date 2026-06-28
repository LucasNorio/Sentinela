let alunosCache = [];

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

async function carregarTurmas() {
  const select = document.querySelector("#turmaAluno");
  const turmas = await requisicao("/api/turmas");

  if (turmas.length === 0) {
    select.innerHTML = '<option value="">Nenhuma turma cadastrada</option>';
    return;
  }

  select.innerHTML = `
    <option value="">Selecione uma turma</option>
    ${turmas
      .map((turma) => {
        return `
        <option value="${turma.id_turma}">
          ${turma.nome} - ${turma.curso}
        </option>
      `;
      })
      .join("")}
  `;
}

async function carregarAlunos() {
  alunosCache = await requisicao("/api/alunos");
  renderizarAlunos();
}

function limparFormularioAluno() {
  document.querySelector("#alunoId").value = "";
  document.querySelector("#nomeAluno").value = "";
  document.querySelector("#matriculaAluno").value = "";
  document.querySelector("#turmaAluno").value = "";
  document.querySelector("#tagAluno").value = "";
  document.querySelector("#statusAluno").value = "Ativo";
}

function preencherFormularioAluno(id) {
  const aluno = alunosCache.find((item) => item.id === id);

  if (!aluno) {
    return;
  }

  document.querySelector("#alunoId").value = aluno.id;
  document.querySelector("#nomeAluno").value = aluno.nome;
  document.querySelector("#matriculaAluno").value = aluno.matricula;
  document.querySelector("#turmaAluno").value = aluno.id_turma;
  document.querySelector("#tagAluno").value = aluno.tag || "";
  document.querySelector("#statusAluno").value = aluno.status;

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

async function inativarAluno(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Aluno concluiu o curso.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm(
    "Deseja realmente inativar este aluno? Ele continuará salvo no histórico do sistema.",
  );

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/alunos/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo: motivo,
      }),
    });

    await carregarAlunos();
  } catch (erro) {
    alert(erro.message);
  }
}

function criarBadgeStatus(status) {
  if (status === "Ativo") {
    return '<span class="badge text-bg-success">Ativo</span>';
  }

  return '<span class="badge text-bg-secondary">Inativo</span>';
}

function renderizarAlunos() {
  const tabela = document.querySelector("#tabelaAlunos");
  const contador = document.querySelector("#contadorAlunos");
  const busca = document
    .querySelector("#buscaAluno")
    .value.trim()
    .toLowerCase();

  let alunos = [...alunosCache];

  if (busca) {
    alunos = alunos.filter((aluno) => {
      const tag = aluno.tag || "";
      const curso = aluno.curso || "";
      const turma = aluno.turma || "";

      return (
        aluno.nome.toLowerCase().includes(busca) ||
        aluno.matricula.toLowerCase().includes(busca) ||
        turma.toLowerCase().includes(busca) ||
        curso.toLowerCase().includes(busca) ||
        tag.toLowerCase().includes(busca)
      );
    });
  }

  contador.textContent = `${alunos.length} aluno${alunos.length === 1 ? "" : "s"}`;

  if (alunos.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">
          Nenhum aluno encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = alunos
    .map((aluno) => {
      return `
      <tr>
        <td>
          <strong>${aluno.nome}</strong>
          <span>${aluno.curso || "Curso não informado"}</span>
        </td>
        <td>${aluno.matricula}</td>
        <td>${aluno.turma || "Turma não informada"}</td>
        <td><code>${aluno.tag || "Sem tag"}</code></td>
        <td>${criarBadgeStatus(aluno.status)}</td>
        <td>
  <div class="table-actions">
    <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioAluno(${aluno.id})">
      Editar
    </button>

    ${
      aluno.status === "Ativo"
        ? `
      <button class="btn btn-outline-secondary btn-sm" onclick="inativarAluno(${aluno.id})">
        Inativar
      </button>
    `
        : `
      <button class="btn btn-outline-success btn-sm" onclick="reativarAluno(${aluno.id})">
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

async function salvarAlunoPeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#alunoId").value;
  const nome = document.querySelector("#nomeAluno").value.trim();
  const matricula = document.querySelector("#matriculaAluno").value.trim();
  const idTurma = document.querySelector("#turmaAluno").value;
  const tag = document.querySelector("#tagAluno").value.trim();
  const status = document.querySelector("#statusAluno").value;

  if (!nome || !matricula || !idTurma || !tag || !status) {
    alert("Preencha todos os campos antes de salvar.");
    return;
  }

  const aluno = {
    nome,
    matricula,
    id_turma: Number(idTurma),
    tag,
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/alunos/${id}`, {
        method: "PUT",
        body: JSON.stringify(aluno),
      });
    } else {
      await requisicao("/api/alunos", {
        method: "POST",
        body: JSON.stringify(aluno),
      });
    }

    limparFormularioAluno();
    await carregarAlunos();
  } catch (erro) {
    alert(erro.message);
  }
}

async function iniciarCadastroAlunos() {
  const form = document.querySelector("#formAluno");
  const busca = document.querySelector("#buscaAluno");
  const btnLimpar = document.querySelector("#btnLimparAluno");

  form.addEventListener("submit", salvarAlunoPeloFormulario);

  busca.addEventListener("input", renderizarAlunos);

  btnLimpar.addEventListener("click", () => {
    limparFormularioAluno();
  });

  try {
    await carregarTurmas();
    await carregarAlunos();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarCadastroAlunos();
});

async function reativarAluno(id) {
  const confirmar = confirm("Deseja realmente reativar este aluno?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/alunos/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarAlunos();
  } catch (erro) {
    alert(erro.message);
  }
}
