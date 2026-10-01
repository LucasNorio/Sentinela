# Changelog

Todas as mudanças relevantes do projeto Sentinela serão documentadas neste arquivo.

---

## [0.4.0] - 2026-10-01

### Adicionado

- Integração física inicial com leitores RFID baseados em ESP32 e MFRC522.
- Firmware dos leitores RFID versionado no repositório:
  - `arduino/sentinela_rfid/sentinela_rfid.ino`
- Comunicação dos leitores RFID com o backend Flask através de Wi-Fi.
- Identificação individual de cada leitor através de código próprio.
- Envio do UID da tag e do código do leitor através de requisições HTTP/JSON.
- Feedback local dos leitores através de:
  - LED verde;
  - LED vermelho;
  - buzzer.
- Registro no monitor serial de:
  - UID da tag;
  - código do leitor;
  - tempo da requisição HTTP;
  - código HTTP retornado;
  - resposta do servidor.
- Módulo de aulas e chamada escolar.
- Tabela `aula` no banco de dados.
- Tabela `presenca` para armazenamento da situação individual dos alunos em cada aula.
- Tabela `ajuste_presenca` para auditoria de correções manuais.
- Campo `id_professor` na tabela `usuario`.
- Vínculo entre usuário com perfil Professor e cadastro acadêmico de professor.
- Funções do professor dentro da turma:
  - Professor;
  - Auxiliar.
- Estados de aula:
  - Programada;
  - Em andamento;
  - Finalizada;
  - Cancelada.
- Estados de presença:
  - Pendente;
  - Presente;
  - Atrasado;
  - Ausente;
  - Justificado.
- Origens de presença:
  - Sistema;
  - RFID;
  - Correção.
- Cadastro e edição de aulas programadas.
- Associação de aulas com:
  - turma;
  - professor;
  - ambiente;
  - data;
  - horário de início;
  - horário de término;
  - tolerância de atraso.
- Validação de conflitos de horário entre:
  - turma;
  - professor;
  - ambiente.
- Cancelamento de aulas programadas com registro de:
  - data do cancelamento;
  - motivo do cancelamento.
- Geração de chamada a partir dos alunos ativos da turma.
- Proteção contra duplicação de presenças ao gerar novamente uma chamada.
- Início controlado de aulas.
- Processamento de registros RFID durante aulas em andamento.
- Classificação automática de presença como:
  - Presente;
  - Atrasado.
- Conversão automática de presenças pendentes para `Ausente` ao finalizar uma chamada.
- Correção manual de presença.
- Obrigatoriedade de motivo para alterações manuais.
- Histórico de ajustes de presença.
- Registro do usuário responsável por cada correção.
- Consulta do histórico de correções pela interface.
- Controle de acesso de Professor por vínculo acadêmico com a turma.
- Suporte ao acesso de professores vinculados como Auxiliar.
- Tela `chamada.html`.
- Arquivo `chamada.js`.
- Arquivo `usuarios.js`.
- Tela `gestao-usuarios.html`.
- Blueprints:
  - `aulas_routes.py`;
  - `auth_routes.py`;
  - `chamadas_routes.py`;
  - `presencas_routes.py`;
  - `usuarios_routes.py`.
- Migration da versão `v0.2.0` para a estrutura da `v0.4.0`.
- Índices adicionais para consultas relacionadas a aulas, presenças e auditoria.
- Script `scripts/criar_usuarios_iniciais.py` para criação dos usuários iniciais.
- Documentação de release em `RELEASE_NOTES_v0.4.0.md`.

### Alterado

- O módulo RFID passou a participar diretamente do fluxo de chamada automática.
- Os registros RFID continuam armazenados separadamente da interpretação de presença.
- Uma leitura RFID agora pode ser utilizada para determinar a presença de um aluno em uma aula em andamento.
- O processamento da presença considera o contexto da aula, incluindo:
  - aluno relacionado;
  - ambiente;
  - horário da leitura;
  - janela válida da aula;
  - tolerância de atraso;
  - estado do aluno;
  - estado da tag;
  - estado do leitor;
  - estado do ambiente;
  - tipo do registro RFID.
- Registros RFID classificados como `Alerta` não são utilizados para confirmar presença.
- O fluxo de chamada passou a seguir o ciclo:

  ```text
  Programada
      ↓
  Gerar chamada
      ↓
  Presenças criadas como Pendente
      ↓
  Iniciar aula
      ↓
  Em andamento
      ↓
  Processar RFID
      ↓
  Presente / Atrasado
      ↓
  Finalizar chamada
      ↓
  Pendentes tornam-se Ausentes
      ↓
  Finalizada