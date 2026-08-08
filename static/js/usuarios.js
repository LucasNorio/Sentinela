let usuarios = [];

const formUsuario = document.querySelector("#formUsuario");
const idUsuario = document.querySelector("#idUsuario");
const nomeUsuarioForm = document.querySelector("#nomeUsuarioForm");
const emailUsuarioForm = document.querySelector("#emailUsuarioForm");
const perfilUsuarioForm = document.querySelector("#perfilUsuarioForm");
const senhaUsuarioForm = document.querySelector("#senhaUsuarioForm");
const grupoSenhaUsuario = document.querySelector("#grupoSenhaUsuario");

const buscaUsuario = document.querySelector("#buscaUsuario");
const filtroPerfilUsuario = document.querySelector("#filtroPerfilUsuario");
const filtroStatusUsuario = document.querySelector("#filtroStatusUsuario");

const btnLimparUsuario = document.querySelector("#btnLimparUsuario");
const btnAtualizarUsuarios = document.querySelector("#btnAtualizarUsuarios");

const tabelaUsuarios = document.querySelector("#tabelaUsuarios");
const contadorUsuarios = document.querySelector("#contadorUsuarios");

async function requisicaoJson(url, opcoes = {}) {
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
    throw new Error(dados.erro || `Erro ${resposta.status} ao processar requisição.`);
  }

  return dados;
}

function montarQueryUsuarios() {
  const parametros = new URLSearchParams();

  if (buscaUsuario.value.trim()) {
    parametros.append("busca", buscaUsuario.value.trim());
  }

  if (filtroPerfilUsuario.value !== "Todos") {
    parametros.append("perfil", filtroPerfilUsuario.value);
  }

  if (filtroStatusUsuario.value !== "Todos") {
    parametros.append("status", filtroStatusUsuario.value);
  }

  const query = parametros.toString();

  return query ? `?${query}` : "";
}

async function carregarUsuarios() {
  try {
    const query = montarQueryUsuarios();

    usuarios = await requisicaoJson(`/api/usuarios${query}`);

    renderizarUsuarios();
  } catch (erro) {
    tabelaUsuarios.innerHTML = `
      <tr>
        <td colspan="6">${erro.message}</td>
      </tr>
    `;
  }
}

function formatarData(data) {
  if (!data) {
    return "-";
  }

  return data;
}

function renderizarUsuarios() {
  contadorUsuarios.textContent = `${usuarios.length} usuário${usuarios.length === 1 ? "" : "s"}`;

  if (!usuarios.length) {
    tabelaUsuarios.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted py-4">
          Nenhum usuário encontrado.
        </td>
      </tr>
    `;
    return;
  }

  tabelaUsuarios.innerHTML = usuarios.map((usuario) => `
    <tr>
      <td>
        <strong>${usuario.nome}</strong>
      </td>

      <td>${usuario.email}</td>

      <td>${usuario.perfil}</td>

      <td>
        <span class="badge rounded-pill ${usuario.status === "Ativo" ? "text-bg-success" : "text-bg-secondary"}">
          ${usuario.status}
        </span>
      </td>

      <td>${formatarData(usuario.ultimo_login)}</td>

      <td>
        <div class="table-actions">
          <button type="button" class="btn btn-sm btn-outline-secondary fw-bold" onclick="editarUsuario(${usuario.id})">
            Editar
          </button>

          <button type="button" class="btn btn-sm btn-outline-secondary fw-bold" onclick="resetarSenhaUsuario(${usuario.id})">
            Resetar senha
          </button>

          ${
            usuario.status === "Ativo"
              ? `<button type="button" class="btn btn-sm btn-outline-danger fw-bold" onclick="inativarUsuario(${usuario.id})">Inativar</button>`
              : `<button type="button" class="btn btn-sm btn-outline-danger fw-bold" onclick="reativarUsuario(${usuario.id})">Reativar</button>`
          }
        </div>
      </td>
    </tr>
  `).join("");
}

function limparFormularioUsuario() {
  idUsuario.value = "";
  nomeUsuarioForm.value = "";
  emailUsuarioForm.value = "";
  perfilUsuarioForm.value = "";
  senhaUsuarioForm.value = "";

  grupoSenhaUsuario.style.display = "block";
  senhaUsuarioForm.disabled = false;

  document.querySelector("#btnSalvarUsuario").textContent = "Salvar usuário";
}

function editarUsuario(id) {
  const usuario = usuarios.find((item) => item.id === id);

  if (!usuario) {
    alert("Usuário não encontrado.");
    return;
  }

  idUsuario.value = usuario.id;
  nomeUsuarioForm.value = usuario.nome;
  emailUsuarioForm.value = usuario.email;
  perfilUsuarioForm.value = usuario.perfil;

  senhaUsuarioForm.value = "";
  senhaUsuarioForm.disabled = true;
  grupoSenhaUsuario.style.display = "none";

  document.querySelector("#btnSalvarUsuario").textContent = "Atualizar usuário";

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

async function salvarUsuario(event) {
  event.preventDefault();

  const id = idUsuario.value;

  const dados = {
    nome: nomeUsuarioForm.value.trim(),
    email: emailUsuarioForm.value.trim(),
    perfil: perfilUsuarioForm.value,
  };

  if (!id) {
    dados.senha = senhaUsuarioForm.value.trim();
  }

  if (!dados.nome || !dados.email || !dados.perfil) {
    alert("Preencha nome, e-mail e perfil.");
    return;
  }

  if (!id && !dados.senha) {
    alert("Informe uma senha inicial.");
    return;
  }

  try {
    if (id) {
      await requisicaoJson(`/api/usuarios/${id}`, {
        method: "PUT",
        body: JSON.stringify(dados),
      });

      alert("Usuário atualizado com sucesso.");
    } else {
      await requisicaoJson("/api/usuarios", {
        method: "POST",
        body: JSON.stringify(dados),
      });

      alert("Usuário criado com sucesso.");
    }

    limparFormularioUsuario();
    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}

async function inativarUsuario(id) {
  const motivo = prompt("Informe o motivo da inativação:");

  if (motivo === null) {
    return;
  }

  try {
    await requisicaoJson(`/api/usuarios/${id}/inativar`, {
      method: "PATCH",
      body: JSON.stringify({
        motivo: motivo.trim() || "Inativação realizada pelo administrador.",
      }),
    });

    alert("Usuário inativado com sucesso.");
    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}

async function reativarUsuario(id) {
  if (!confirm("Deseja reativar este usuário?")) {
    return;
  }

  try {
    await requisicaoJson(`/api/usuarios/${id}/reativar`, {
      method: "PATCH",
    });

    alert("Usuário reativado com sucesso.");
    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}

async function resetarSenhaUsuario(id) {
  const novaSenha = prompt("Informe a nova senha do usuário:");

  if (novaSenha === null) {
    return;
  }

  if (novaSenha.trim().length < 6) {
    alert("A senha deve ter pelo menos 6 caracteres.");
    return;
  }

  try {
    await requisicaoJson(`/api/usuarios/${id}/resetar-senha`, {
      method: "PATCH",
      body: JSON.stringify({
        nova_senha: novaSenha.trim(),
      }),
    });

    alert("Senha redefinida com sucesso.");
  } catch (erro) {
    alert(erro.message);
  }
}

formUsuario.addEventListener("submit", salvarUsuario);
btnLimparUsuario.addEventListener("click", limparFormularioUsuario);
btnAtualizarUsuarios.addEventListener("click", carregarUsuarios);

buscaUsuario.addEventListener("input", carregarUsuarios);
filtroPerfilUsuario.addEventListener("change", carregarUsuarios);
filtroStatusUsuario.addEventListener("change", carregarUsuarios);

document.addEventListener("DOMContentLoaded", carregarUsuarios);