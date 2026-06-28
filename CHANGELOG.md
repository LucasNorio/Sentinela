# Changelog

Todas as mudanças relevantes do projeto serão documentadas neste arquivo.

## v0.1.2 — versão de apresentação

Foco: melhorar a apresentação pública do projeto no GitHub sem alterar a lógica principal do sistema.

### Adicionado

- README mais completo e orientado para apresentação do projeto.
- Pasta `docs/` com documentação complementar.
- Pasta `assets/screenshots/` com capturas das principais telas.
- `CHANGELOG.md`.
- `RELEASE_NOTES_v0.1.2.md`.
- Documentação do fluxo RFID.
- Documentação da arquitetura inicial.
- Documentação das APIs principais.
- Roadmap de evolução por versões.

### Alterado

- Padronização visual de versão para `0.1.2`.
- Texto do projeto ajustado para apresentação pública.

### Não alterado

- Regras de negócio.
- Rotas principais.
- Estrutura do banco.
- CRUDs existentes.
- Fluxo de registro RFID.

## v0.1.1 — limpeza da primeira versão funcional

Foco: limpar o projeto para publicação inicial no GitHub.

### Adicionado

- `.env.example`.
- `.gitignore`.
- `README.md` inicial.
- `database/schema.sql`.
- `database/seed.sql`.

### Removido

- Ambientes virtuais locais.
- `node_modules`.
- Arquivos de cache.
- `.env` real.
- Scripts antigos de dados simulados das páginas principais.

### Alterado

- Padronização de textos de versão.
- Remoção de referências antigas a dados simulados.

## v0.1.0 — primeira base funcional

Foco: construir o fluxo principal do sistema integrado ao banco.

### Implementado

- Cadastro de alunos.
- Cadastro de professores.
- Gestão de cursos e turmas.
- Vínculo professor-turma.
- Gestão de ambientes.
- Gestão de leitores RFID.
- Registro RFID por API.
- Histórico real de movimentações.
- Dashboard com dados reais.
- Mapa com ambientes e leitores reais.
