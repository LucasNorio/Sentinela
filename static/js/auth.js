async function requisicaoAuth(url, opcoes = {}) {
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
      dados.erro || `Erro ${resposta.status} ao processar a requisição.`
    );
  }

  return dados;
}

function obterElementosLogin() {
  return {
    form:
      document.querySelector("#formLogin") ||
      document.querySelector("#loginForm") ||
      document.querySelector("form"),
    email:
      document.querySelector("#email") ||
      document.querySelector("#emailLogin") ||
      document.querySelector('input[type="email"]'),
    senha:
      document.querySelector("#senha") ||
      document.querySelector("#senhaLogin") ||
      document.querySelector('input[type="password"]'),
  };
}

function atualizarPainelUsuario(usuario) {
  const nomeUsuario = document.querySelector("#nomeUsuario");
  const cargoUsuario = document.querySelector("#cargoUsuario");
  const avatarUsuario = document.querySelector("#avatarUsuario");

  if (nomeUsuario) {
    nomeUsuario.textContent = usuario.nome;
  }

  if (cargoUsuario) {
    cargoUsuario.textContent = usuario.perfil;
  }

  if (avatarUsuario && usuario.nome) {
    avatarUsuario.textContent = usuario.nome.charAt(0).toUpperCase();
  }
}

function obterRotasPermitidasPorPerfil(perfil) {
  const rotasComuns = [
    "/home",
    "/mapa",
    "/historico",
    "/sobre",
  ];

  const rotasGestao = [
    "/cadastro-professores",
    "/cadastro-alunos",
    "/gestao-academica",
    "/gestao-ambientes",
    "/gestao-leitores",
  ];

  const rotasAdmin = [
    "/administracao",
    "/gestao-usuarios",
  ];

  if (perfil === "Administrador") {
    return [
      ...rotasComuns,
      ...rotasGestao,
      ...rotasAdmin,
    ];
  }

  if (perfil === "Coordenação" || perfil === "Secretaria") {
    return [
      ...rotasComuns,
      ...rotasGestao,
    ];
  }

  if (perfil === "Professor") {
    return rotasComuns;
  }

  return [];
}

function esconderElementoDeNavegacao(link) {
  const card =
    link.closest(".card") ||
    link.closest(".dashboard-card") ||
    link.closest(".module-card") ||
    link.closest(".action-card") ||
    link.closest(".menu-card") ||
    link.closest(".col") ||
    link;

  card.style.display = "none";
}

function aplicarPermissoesInterface(usuario) {
  const rotasPermitidas = obterRotasPermitidasPorPerfil(usuario.perfil);

  const links = document.querySelectorAll("a[href]");

  links.forEach((link) => {
    const href = link.getAttribute("href");

    if (!href || href.startsWith("http") || href.startsWith("#")) {
      return;
    }

    if (href === "/" || href === "/sair") {
      return;
    }

    if (!rotasPermitidas.includes(href)) {
      esconderElementoDeNavegacao(link);
    }
  });

  const elementosComRota = document.querySelectorAll("[data-rota]");

  elementosComRota.forEach((elemento) => {
    const rota = elemento.getAttribute("data-rota");

    if (!rotasPermitidas.includes(rota)) {
      elemento.style.display = "none";
    }
  });
}

async function verificarSessao() {
  const paginaProtegida = document.body.dataset.page === "protected";

  if (!paginaProtegida) {
    return;
  }

  try {
    const dados = await requisicaoAuth("/api/auth/me");

    atualizarPainelUsuario(dados.usuario);
    aplicarPermissoesInterface(dados.usuario);
  } catch {
    window.location.href = "/";
  }
}

async function realizarLogin(event) {
  event.preventDefault();

  const { email, senha } = obterElementosLogin();

  const emailValor = email.value.trim();
  const senhaValor = senha.value.trim();

  if (!emailValor || !senhaValor) {
    alert("Informe o e-mail e a senha para acessar o sistema.");
    return;
  }

  try {
    await requisicaoAuth("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: emailValor,
        senha: senhaValor,
      }),
    });

    window.location.href = "/home";
  } catch (erro) {
    alert(erro.message);
  }
}

async function realizarLogout() {
  try {
    await requisicaoAuth("/api/auth/logout", {
      method: "POST",
    });
  } catch {
  } finally {
    window.location.href = "/";
  }
}

function iniciarLogin() {
  const paginaProtegida = document.body.dataset.page === "protected";
  const { form, email, senha } = obterElementosLogin();

  if (!paginaProtegida && form && email && senha) {
    form.addEventListener("submit", realizarLogin);
  }
}

function iniciarLogout() {
  const btnSair = document.querySelector("#btnSair");

  if (btnSair) {
    btnSair.addEventListener("click", realizarLogout);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarLogin();
  iniciarLogout();
  verificarSessao();
});