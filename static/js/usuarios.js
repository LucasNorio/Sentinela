let usuarios = [];
let professores = [];

const formUsuario =
  document.querySelector("#formUsuario");

const idUsuario =
  document.querySelector("#idUsuario");

const nomeUsuarioForm =
  document.querySelector("#nomeUsuarioForm");

const emailUsuarioForm =
  document.querySelector("#emailUsuarioForm");

const perfilUsuarioForm =
  document.querySelector("#perfilUsuarioForm");

const senhaUsuarioForm =
  document.querySelector("#senhaUsuarioForm");

const grupoSenhaUsuario =
  document.querySelector("#grupoSenhaUsuario");

const grupoProfessorUsuario =
  document.querySelector("#grupoProfessorUsuario");

const professorUsuarioForm =
  document.querySelector("#professorUsuarioForm");

const buscaUsuario =
  document.querySelector("#buscaUsuario");

const filtroPerfilUsuario =
  document.querySelector("#filtroPerfilUsuario");

const filtroStatusUsuario =
  document.querySelector("#filtroStatusUsuario");

const btnLimparUsuario =
  document.querySelector("#btnLimparUsuario");

const btnAtualizarUsuarios =
  document.querySelector("#btnAtualizarUsuarios");

const tabelaUsuarios =
  document.querySelector("#tabelaUsuarios");

const contadorUsuarios =
  document.querySelector("#contadorUsuarios");


async function requisicaoJson(
  url,
  opcoes = {}
) {
  const resposta = await fetch(url, {
    credentials: "same-origin",
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
      dados.erro ||
      `Erro ${resposta.status} ao processar requisição.`
    );
  }

  return dados;
}


function montarQueryUsuarios() {
  const parametros = new URLSearchParams();

  if (buscaUsuario.value.trim()) {
    parametros.append(
      "busca",
      buscaUsuario.value.trim()
    );
  }

  if (
    filtroPerfilUsuario.value !== "Todos"
  ) {
    parametros.append(
      "perfil",
      filtroPerfilUsuario.value
    );
  }

  if (
    filtroStatusUsuario.value !== "Todos"
  ) {
    parametros.append(
      "status",
      filtroStatusUsuario.value
    );
  }

  const query = parametros.toString();

  return query
    ? `?${query}`
    : "";
}


async function carregarUsuarios() {
  try {
    const query = montarQueryUsuarios();

    usuarios = await requisicaoJson(
      `/api/usuarios${query}`
    );

    renderizarUsuarios();
  } catch (erro) {
    tabelaUsuarios.innerHTML = `
      <tr>
        <td colspan="6">
          ${erro.message}
        </td>
      </tr>
    `;
  }
}


async function carregarProfessores() {
  try {
    const dados = await requisicaoJson(
      "/api/professores"
    );

    professores = Array.isArray(dados)
      ? dados
      : dados.professores || [];

    renderizarProfessoresFormulario();
  } catch (erro) {
    console.error(
      "Erro ao carregar professores:",
      erro
    );

    professores = [];
  }
}


function renderizarProfessoresFormulario() {
  professorUsuarioForm.innerHTML = `
    <option value="">
      Selecione o professor
    </option>
  `;

  const professoresAtivos =
    professores.filter(
      (professor) =>
        professor.status === "Ativo"
    );

  professoresAtivos.forEach(
    (professor) => {
      professorUsuarioForm.innerHTML += `
        <option value="${professor.id}">
          ${professor.nome}
        </option>
      `;
    }
  );
}


function atualizarCampoProfessor() {
  const perfil = perfilUsuarioForm.value;

  if (perfil === "Professor") {
    grupoProfessorUsuario.style.display =
      "block";

    professorUsuarioForm.required = true;

    return;
  }

  grupoProfessorUsuario.style.display =
    "none";

  professorUsuarioForm.required = false;
  professorUsuarioForm.value = "";
}


function formatarData(data) {
  if (!data) {
    return "-";
  }

  return data;
}


function renderizarUsuarios() {
  contadorUsuarios.textContent =
    `${usuarios.length} usuário${
      usuarios.length === 1
        ? ""
        : "s"
    }`;

  if (!usuarios.length) {
    tabelaUsuarios.innerHTML = `
      <tr>
        <td
          colspan="6"
          class="text-center text-muted py-4"
        >
          Nenhum usuário encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabelaUsuarios.innerHTML =
    usuarios.map(
      (usuario) => `
        <tr>
          <td>
            <strong>
              ${usuario.nome}
            </strong>
          </td>

          <td>
            ${usuario.email}
          </td>

          <td>
            ${usuario.perfil}

            ${
              usuario.perfil === "Professor"
                ? `
                  <small
                    class="d-block text-muted mt-1"
                  >
                    ${
                      usuario.professor
                        || "Sem vínculo"
                    }
                  </small>
                `
                : ""
            }
          </td>

          <td>
            <span
              class="badge rounded-pill ${
                usuario.status === "Ativo"
                  ? "text-bg-success"
                  : "text-bg-secondary"
              }"
            >
              ${usuario.status}
            </span>
          </td>

          <td>
            ${formatarData(
              usuario.ultimo_login
            )}
          </td>

          <td>
            <div class="table-actions">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary fw-bold"
                onclick="editarUsuario(${usuario.id})"
              >
                Editar
              </button>

              <button
                type="button"
                class="btn btn-sm btn-outline-secondary fw-bold"
                onclick="resetarSenhaUsuario(${usuario.id})"
              >
                Resetar senha
              </button>

              ${
                usuario.status === "Ativo"
                  ? `
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-danger fw-bold"
                      onclick="inativarUsuario(${usuario.id})"
                    >
                      Inativar
                    </button>
                  `
                  : `
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-danger fw-bold"
                      onclick="reativarUsuario(${usuario.id})"
                    >
                      Reativar
                    </button>
                  `
              }
            </div>
          </td>
        </tr>
      `
    ).join("");
}


function limparFormularioUsuario() {
  idUsuario.value = "";
  nomeUsuarioForm.value = "";
  emailUsuarioForm.value = "";
  perfilUsuarioForm.value = "";
  senhaUsuarioForm.value = "";
  professorUsuarioForm.value = "";

  grupoSenhaUsuario.style.display =
    "block";

  senhaUsuarioForm.disabled = false;

  document.querySelector(
    "#btnSalvarUsuario"
  ).textContent = "Salvar usuário";

  atualizarCampoProfessor();
}


function editarUsuario(id) {
  const usuario = usuarios.find(
    (item) => item.id === id
  );

  if (!usuario) {
    alert("Usuário não encontrado.");
    return;
  }

  idUsuario.value = usuario.id;

  nomeUsuarioForm.value =
    usuario.nome;

  emailUsuarioForm.value =
    usuario.email;

  perfilUsuarioForm.value =
    usuario.perfil;

  atualizarCampoProfessor();

  if (
    usuario.perfil === "Professor"
    && usuario.id_professor
  ) {
    professorUsuarioForm.value =
      String(usuario.id_professor);
  }

  senhaUsuarioForm.value = "";
  senhaUsuarioForm.disabled = true;

  grupoSenhaUsuario.style.display =
    "none";

  document.querySelector(
    "#btnSalvarUsuario"
  ).textContent =
    "Atualizar usuário";

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}


async function salvarUsuario(event) {
  event.preventDefault();

  const id = idUsuario.value;

  const dados = {
    nome:
      nomeUsuarioForm.value.trim(),

    email:
      emailUsuarioForm.value.trim(),

    perfil:
      perfilUsuarioForm.value,

    id_professor:
      perfilUsuarioForm.value ===
      "Professor"
        ? Number(
            professorUsuarioForm.value
          )
        : null,
  };

  if (!id) {
    dados.senha =
      senhaUsuarioForm.value.trim();
  }

  if (
    !dados.nome
    || !dados.email
    || !dados.perfil
  ) {
    alert(
      "Preencha nome, e-mail e perfil."
    );

    return;
  }

  if (
    dados.perfil === "Professor"
    && !dados.id_professor
  ) {
    alert(
      "Selecione o cadastro de professor."
    );

    return;
  }

  if (!id && !dados.senha) {
    alert(
      "Informe uma senha inicial."
    );

    return;
  }

  try {
    let resposta;

    if (id) {
      resposta = await requisicaoJson(
        `/api/usuarios/${id}`,
        {
          method: "PUT",
          body: JSON.stringify(dados),
        }
      );
    } else {
      resposta = await requisicaoJson(
        "/api/usuarios",
        {
          method: "POST",
          body: JSON.stringify(dados),
        }
      );
    }

    alert(
      resposta.mensagem
      || "Operação realizada com sucesso."
    );

    limparFormularioUsuario();

    await carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}


async function inativarUsuario(id) {
  const motivo = prompt(
    "Informe o motivo da inativação:"
  );

  if (motivo === null) {
    return;
  }

  try {
    await requisicaoJson(
      `/api/usuarios/${id}/inativar`,
      {
        method: "PATCH",
        body: JSON.stringify({
          motivo:
            motivo.trim()
            || "Inativação realizada pelo administrador.",
        }),
      }
    );

    alert(
      "Usuário inativado com sucesso."
    );

    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}


async function reativarUsuario(id) {
  if (
    !confirm(
      "Deseja reativar este usuário?"
    )
  ) {
    return;
  }

  try {
    await requisicaoJson(
      `/api/usuarios/${id}/reativar`,
      {
        method: "PATCH",
      }
    );

    alert(
      "Usuário reativado com sucesso."
    );

    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}


async function resetarSenhaUsuario(id) {
  const novaSenha = prompt(
    "Informe a nova senha do usuário:"
  );

  if (novaSenha === null) {
    return;
  }

  if (
    novaSenha.trim().length < 6
  ) {
    alert(
      "A senha deve ter pelo menos 6 caracteres."
    );

    return;
  }

  try {
    await requisicaoJson(
      `/api/usuarios/${id}/resetar-senha`,
      {
        method: "PATCH",
        body: JSON.stringify({
          nova_senha:
            novaSenha.trim(),
        }),
      }
    );

    alert(
      "Senha redefinida com sucesso."
    );
  } catch (erro) {
    alert(erro.message);
  }
}


formUsuario.addEventListener(
  "submit",
  salvarUsuario
);

btnLimparUsuario.addEventListener(
  "click",
  limparFormularioUsuario
);

btnAtualizarUsuarios.addEventListener(
  "click",
  carregarUsuarios
);

perfilUsuarioForm.addEventListener(
  "change",
  atualizarCampoProfessor
);

buscaUsuario.addEventListener(
  "input",
  carregarUsuarios
);

filtroPerfilUsuario.addEventListener(
  "change",
  carregarUsuarios
);

filtroStatusUsuario.addEventListener(
  "change",
  carregarUsuarios
);


document.addEventListener(
  "DOMContentLoaded",
  async () => {
    await carregarProfessores();

    atualizarCampoProfessor();

    await carregarUsuarios();
  }
);
