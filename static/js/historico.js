let registrosCache = [];

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

function criarBadgeTipoRegistro(tipo) {
  if (tipo === "Entrada") {
    return '<span class="badge text-bg-success">Entrada</span>';
  }

  if (tipo === "Saída") {
    return '<span class="badge text-bg-primary">Saída</span>';
  }

  if (tipo === "Alerta") {
    return '<span class="badge text-bg-danger">Alerta</span>';
  }

  return '<span class="badge text-bg-secondary">Movimentação</span>';
}

function formatarDataHora(valor) {
  if (!valor) {
    return "Não informado";
  }

  const data = new Date(valor.replace(" ", "T"));

  if (Number.isNaN(data.getTime())) {
    return valor;
  }

  return data.toLocaleString("pt-BR");
}

function textoSeguro(valor, fallback = "Não informado") {
  if (valor === null || valor === undefined || valor === "") {
    return fallback;
  }

  return valor;
}

async function carregarRegistros() {
  registrosCache = await requisicao("/api/registros-rfid?limite=300");
  atualizarResumoHistorico();
  renderizarRegistros();
}

function atualizarResumoHistorico() {
  const total = registrosCache.length;
  const entradas = registrosCache.filter(
    (registro) => registro.tipo === "Entrada",
  ).length;
  const saidas = registrosCache.filter(
    (registro) => registro.tipo === "Saída",
  ).length;
  const alertas = registrosCache.filter(
    (registro) => registro.tipo === "Alerta",
  ).length;

  document.querySelector("#totalRegistrosHistorico").textContent = total;
  document.querySelector("#totalEntradasHistorico").textContent = entradas;
  document.querySelector("#totalSaidasHistorico").textContent = saidas;
  document.querySelector("#totalAlertasHistorico").textContent = alertas;
}

function renderizarRegistros() {
  const tabela = document.querySelector("#tabelaRegistros");
  const contador = document.querySelector("#contadorRegistros");
  const busca = document.querySelector("#buscaRegistro").value.trim().toLowerCase();
  const filtroTipo = document.querySelector("#filtroTipoRegistro").value;

  let registros = [...registrosCache];

  if (filtroTipo !== "Todos") {
    registros = registros.filter((registro) => registro.tipo === filtroTipo);
  }

  if (busca) {
    registros = registros.filter((registro) => {
      const aluno = String(registro.aluno || "").toLowerCase();
      const tagLida = String(registro.codigo_tag_lida || "").toLowerCase();
      const tagCadastrada = String(
        registro.codigo_tag_cadastrada || "",
      ).toLowerCase();
      const leitor = String(registro.leitor || "").toLowerCase();
      const codigoLeitor = String(registro.codigo_leitor || "").toLowerCase();
      const ambiente = String(registro.ambiente || "").toLowerCase();
      const bloco = String(registro.bloco || "").toLowerCase();
      const observacao = String(registro.observacao || "").toLowerCase();
      const tipo = String(registro.tipo || "").toLowerCase();

      return (
        aluno.includes(busca) ||
        tagLida.includes(busca) ||
        tagCadastrada.includes(busca) ||
        leitor.includes(busca) ||
        codigoLeitor.includes(busca) ||
        ambiente.includes(busca) ||
        bloco.includes(busca) ||
        observacao.includes(busca) ||
        tipo.includes(busca)
      );
    });
  }

  contador.textContent = `${registros.length} registro${
    registros.length === 1 ? "" : "s"
  }`;

  if (registros.length === 0) {
    tabela.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-secondary py-4">
          Nenhum registro RFID encontrado.
        </td>
      </tr>
    `;

    return;
  }

  tabela.innerHTML = registros
    .map((registro) => {
      const aluno = textoSeguro(registro.aluno, "Aluno não identificado");
      const tag = textoSeguro(registro.codigo_tag_lida);
      const leitor = textoSeguro(registro.leitor);
      const ambiente = textoSeguro(registro.ambiente);
      const bloco = textoSeguro(registro.bloco, "");
      const observacao = textoSeguro(registro.observacao, "Sem observação");

      return `
        <tr>
          <td>
            <strong>${formatarDataHora(registro.data_hora)}</strong>
            <span>ID #${registro.id}</span>
          </td>

          <td>
            <strong>${aluno}</strong>
            <span>${textoSeguro(registro.status_aluno, "Status desconhecido")}</span>
          </td>

          <td>
            <code>${tag}</code>
            <span>${textoSeguro(registro.status_tag, "Tag não cadastrada")}</span>
          </td>

          <td>
            ${leitor}
            <span>${textoSeguro(registro.codigo_leitor, "")}</span>
          </td>

          <td>
            ${ambiente}
            <span>${bloco}</span>
          </td>

          <td>
            ${criarBadgeTipoRegistro(registro.tipo)}
          </td>

          <td>
            ${observacao}
          </td>
        </tr>
      `;
    })
    .join("");
}

async function iniciarHistorico() {
  const buscaRegistro = document.querySelector("#buscaRegistro");
  const filtroTipoRegistro = document.querySelector("#filtroTipoRegistro");
  const btnAtualizarHistorico = document.querySelector("#btnAtualizarHistorico");

  buscaRegistro.addEventListener("input", renderizarRegistros);
  filtroTipoRegistro.addEventListener("change", renderizarRegistros);

  btnAtualizarHistorico.addEventListener("click", async () => {
    try {
      await carregarRegistros();
    } catch (erro) {
      alert(erro.message);
    }
  });

  try {
    await carregarRegistros();
  } catch (erro) {
    alert(erro.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarHistorico();
});