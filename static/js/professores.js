let professoresCache = [];

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

function obterNumerosTelefone(valor) {
  return String(valor || "").replace(/\D/g, "");
}

function formatarTelefoneProfessor(valor) {
  const numeros = obterNumerosTelefone(valor).slice(0, 11);

  if (numeros.length === 0) {
    return "";
  }

  if (numeros.length <= 2) {
    return `(${numeros}`;
  }

  const ddd = numeros.slice(0, 2);
  const restante = numeros.slice(2);

  if (numeros.length <= 6) {
    return `(${ddd}) ${restante}`;
  }

  if (numeros.length <= 10) {
    return `(${ddd}) ${restante.slice(0, 4)}-${restante.slice(4)}`;
  }

  return `(${ddd}) ${restante.slice(0, 5)}-${restante.slice(5)}`;
}

function telefoneProfessorValido(telefone) {
  const numeros = obterNumerosTelefone(telefone);

  return numeros.length === 10 || numeros.length === 11;
}

async function carregarProfessores() {
  professoresCache = await requisicao("/api/professores");
  renderizarProfessores();
}

function limparFormularioProfessor() {
  document.querySelector("#professorId").value = "";
  document.querySelector("#nomeProfessor").value = "";
  document.querySelector("#emailProfessor").value = "";
  document.querySelector("#registroProfessor").value = "";
  document.querySelector("#areaProfessor").value = "";
  document.querySelector("#telefoneProfessor").value = "";
  document.querySelector("#statusProfessor").value = "Ativo";
}

function preencherFormularioProfessor(id) {
  const professor = professoresCache.find((item) => item.id === id);

  if (!professor) {
    return;
  }

  document.querySelector("#professorId").value = professor.id;
  document.querySelector("#nomeProfessor").value = professor.nome;
  document.querySelector("#emailProfessor").value = professor.email;
  document.querySelector("#registroProfessor").value =
    professor.registro_professor;
  document.querySelector("#areaProfessor").value = professor.area;
  document.querySelector("#telefoneProfessor").value = formatarTelefoneProfessor(
    professor.telefone || "",
  );
  document.querySelector("#statusProfessor").value = professor.status;

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

async function inativarProfessor(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:",
    "Professor inativado pelo sistema.",
  );

  if (motivo === null) {
    return;
  }

  const confirmar = confirm(
    "Deseja realmente inativar este professor? Ele continuará salvo no histórico do sistema.",
  );

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/professores/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo,
      }),
    });

    await carregarProfessores();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarProfessor(id) {
  const confirmar = confirm("Deseja realmente reativar este professor?");

  if (!confirmar) {
    return;
  }

  try {
    await requisicao(`/api/professores/${id}/reativar`, {
      method: "PATCH",
    });

    await carregarProfessores();
  } catch (erro) {
    alert(erro.message);
  }
}

function criarBadgeStatusProfessor(status) {
  if (status === "Ativo") {
    return '<span class="badge text-bg-success">Ativo</span>';
  }

  return '<span class="badge text-bg-secondary">Inativo</span>';
}

function renderizarProfessores() {
  const tabela = document.querySelector("#tabelaProfessores");
  const contador = document.querySelector("#contadorProfessores");
  const busca = document
    .querySelector("#buscaProfessor")
    .value.trim()
    .toLowerCase();

  let professores = [...professoresCache];

  if (busca) {
    professores = professores.filter((professor) => {
      const telefone = professor.telefone || "";
      const telefoneFormatado = formatarTelefoneProfessor(telefone);

      return (
        professor.nome.toLowerCase().includes(busca) ||
        professor.email.toLowerCase().includes(busca) ||
        professor.registro_professor.toLowerCase().includes(busca) ||
        professor.area.toLowerCase().includes(busca) ||
        telefone.toLowerCase().includes(busca) ||
        telefoneFormatado.toLowerCase().includes(busca)
      );
    });
  }

  contador.textContent = `${professores.length} professor${professores.length === 1 ? "" : "es"}`;

  if (professores.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-secondary py-4">
          Nenhum professor encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = professores
    .map((professor) => {
      const telefone = professor.telefone
        ? formatarTelefoneProfessor(professor.telefone)
        : "Não informado";

      return `
      <tr>
        <td>
          <strong>${professor.nome}</strong>
          <span>${professor.email}</span>
        </td>
        <td>${professor.registro_professor}</td>
        <td>${professor.area}</td>
        <td>${telefone}</td>
        <td>${criarBadgeStatusProfessor(professor.status)}</td>
        <td>
          <div class="table-actions">
            <button class="btn btn-outline-danger btn-sm" onclick="preencherFormularioProfessor(${professor.id})">
              Editar
            </button>

            ${
              professor.status === "Ativo"
                ? `
              <button class="btn btn-outline-secondary btn-sm" onclick="inativarProfessor(${professor.id})">
                Inativar
              </button>
            `
                : `
              <button class="btn btn-outline-success btn-sm" onclick="reativarProfessor(${professor.id})">
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

async function salvarProfessorPeloFormulario(event) {
  event.preventDefault();

  const id = document.querySelector("#professorId").value;
  const nome = document.querySelector("#nomeProfessor").value.trim();
  const email = document.querySelector("#emailProfessor").value.trim();
  const registroProfessor = document
    .querySelector("#registroProfessor")
    .value.trim();
  const area = document.querySelector("#areaProfessor").value.trim();
  const telefone = document.querySelector("#telefoneProfessor").value.trim();
  const status = document.querySelector("#statusProfessor").value;

  if (!nome || !email || !registroProfessor || !area || !status) {
    alert("Preencha todos os campos obrigatórios antes de salvar.");
    return;
  }

  if (telefone && !telefoneProfessorValido(telefone)) {
    alert("Informe um telefone válido com DDD. Exemplo: (14) 99999-9999.");
    return;
  }

  const professor = {
    nome,
    email,
    registro_professor: registroProfessor,
    area,
    telefone: formatarTelefoneProfessor(telefone),
    status,
  };

  try {
    if (id) {
      await requisicao(`/api/professores/${id}`, {
        method: "PUT",
        body: JSON.stringify(professor),
      });
    } else {
      await requisicao("/api/professores", {
        method: "POST",
        body: JSON.stringify(professor),
      });
    }

    limparFormularioProfessor();
    await carregarProfessores();
  } catch (erro) {
    alert(erro.message);
  }
}

async function iniciarCadastroProfessores() {
  const form = document.querySelector("#formProfessor");
  const busca = document.querySelector("#buscaProfessor");
  const btnLimpar = document.querySelector("#btnLimparProfessor");
  const telefoneInput = document.querySelector("#telefoneProfessor");

  form.addEventListener("submit", salvarProfessorPeloFormulario);

  busca.addEventListener("input", renderizarProfessores);

  btnLimpar.addEventListener("click", () => {
    limparFormularioProfessor();
  });

  telefoneInput.addEventListener("input", () => {
    telefoneInput.value = formatarTelefoneProfessor(telefoneInput.value);
  });

  telefoneInput.addEventListener("paste", () => {
    setTimeout(() => {
      telefoneInput.value = formatarTelefoneProfessor(telefoneInput.value);
    }, 0);
  });

  try {
    await carregarProfessores();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarCadastroProfessores();
});