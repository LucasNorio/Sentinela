const USUARIO_TESTE = {
  email: 'adminsentinela@gmail.com',
  senha: 'adminsentinela'
}

const SESSION_KEY = 'sentinela_usuario_logado'

function obterUsuarioLogado() {
  const usuario = localStorage.getItem(SESSION_KEY)

  if (!usuario) {
    return null
  }

  return JSON.parse(usuario)
}

function salvarUsuarioLogado(email) {
  const usuario = {
    email: email,
    nome: 'Administrador',
    cargo: 'Secretaria / Coordenação',
    unidade: 'SENAI Botucatu',
    loginEm: new Date().toISOString()
  }

  localStorage.setItem(SESSION_KEY, JSON.stringify(usuario))
}

function iniciarLogin() {
  const form = document.querySelector('#loginForm')
  const alert = document.querySelector('#loginAlert')

  if (!form) {
    return
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault()

    const email = document.querySelector('#email').value.trim().toLowerCase()
    const senha = document.querySelector('#senha').value.trim()

    if (email === USUARIO_TESTE.email && senha === USUARIO_TESTE.senha) {
      salvarUsuarioLogado(email)
      window.location.href = '/home'
      return
    }

    alert.textContent = 'E-mail ou senha inválidos. Confira as credenciais de teste e tente novamente.'
    alert.classList.remove('d-none')
  })
}

function protegerPagina() {
  const usuario = obterUsuarioLogado()

  if (!usuario) {
    window.location.href = '/'
    return null
  }

  return usuario
}

function renderizarUsuarioLogado() {
  const usuario = obterUsuarioLogado()

  if (!usuario) {
    return
  }

  const nomeUsuario = document.querySelector('#nomeUsuario')
  const cargoUsuario = document.querySelector('#cargoUsuario')
  const unidadeUsuario = document.querySelector('#unidadeUsuario')
  const saudacaoUsuario = document.querySelector('#saudacaoUsuario')
  const avatarUsuario = document.querySelector('#avatarUsuario')

  if (nomeUsuario) {
    nomeUsuario.textContent = usuario.nome
  }

  if (cargoUsuario) {
    cargoUsuario.textContent = usuario.cargo
  }

  if (unidadeUsuario) {
    unidadeUsuario.textContent = usuario.unidade
  }

  if (saudacaoUsuario) {
    saudacaoUsuario.textContent = `Olá, ${usuario.nome}`
  }

  if (avatarUsuario) {
    avatarUsuario.textContent = usuario.nome.charAt(0).toUpperCase()
  }
}

function sairDoSistema() {
  localStorage.removeItem(SESSION_KEY)
  window.location.href = '/'
}

function iniciarBotaoSair() {
  const botaoSair = document.querySelector('#btnSair')

  if (!botaoSair) {
    return
  }

  botaoSair.addEventListener('click', () => {
    sairDoSistema()
  })
}

document.addEventListener('DOMContentLoaded', () => {
  const pagina = document.body.dataset.page

  if (pagina === 'login') {
    iniciarLogin()
  }

  if (pagina === 'protected') {
    const usuario = protegerPagina()

    if (usuario) {
      renderizarUsuarioLogado()
      iniciarBotaoSair()
    }
  }
})