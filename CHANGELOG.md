# Changelog

Todas as mudanças relevantes do projeto Sentinela serão documentadas neste arquivo.

## [0.2.0] - 2026-08-07

### Adicionado

- Autenticação real com dados armazenados no banco MySQL.
- Tabela `usuario` no `schema.sql`.
- Campo `senha_hash` para armazenamento seguro de senhas.
- Uso de hash de senha com Werkzeug Security.
- Sessão Flask para controle de usuário autenticado.
- Endpoint de login:
  - `POST /api/auth/login`
- Endpoint de logout:
  - `POST /api/auth/logout`
- Endpoint para consultar usuário autenticado:
  - `GET /api/auth/me`
- Registro de último login do usuário.
- Controle de permissões por perfil:
  - Administrador
  - Coordenação
  - Secretaria
  - Professor
- Proteção de páginas internas.
- Proteção de APIs internas.
- Controle visual de menus por perfil.
- Controle visual de cards por perfil.
- API de gestão de usuários:
  - `GET /api/usuarios`
  - `POST /api/usuarios`
  - `PUT /api/usuarios/<id>`
  - `PATCH /api/usuarios/<id>/inativar`
  - `PATCH /api/usuarios/<id>/reativar`
  - `PATCH /api/usuarios/<id>/resetar-senha`
- Tela `gestao-usuarios.html`.
- Script `scripts/criar_usuarios_iniciais.py`.
- Usuários iniciais de desenvolvimento:
  - Administrador
  - Coordenação
  - Secretaria
  - Professor
- Card de Gestão de Usuários na página Administração.
- Página Sobre atualizada para a versão 0.2.0.
- Textos visuais de versão atualizados para 0.2.0.
- Documentação de instalação atualizada para criação de usuários iniciais.

### Alterado

- O login deixou de ser apenas visual/local e passou a usar autenticação real pelo banco.
- O fluxo de instalação agora inclui:
  - criação do banco pelo `schema.sql`;
  - carga inicial pelo `seed.sql`;
  - criação de usuários pelo script Python.
- O comando de instalação das dependências passou a usar `python -m pip install -r requirements.txt`, evitando problemas com `pip` não reconhecido no Windows.
- A página Administração passou a incluir acesso ao módulo de Gestão de Usuários.
- A interface passou a esconder links e cards de acordo com o perfil do usuário autenticado.
- O `README.md` foi atualizado para refletir a versão 0.2.0.

### Corrigido

- Acesso direto a páginas internas sem autenticação.
- Acesso direto a APIs internas sem autenticação.
- Inconsistências de versão visual entre páginas.
- Problemas de exibição de permissões no menu lateral.
- Exibição de cards administrativos para usuários sem permissão.
- Falha de importação no script de criação de usuários quando executado dentro da pasta `scripts`.

### Segurança

- Senhas não são armazenadas em texto puro.
- Usuários inativos não conseguem realizar login.
- APIs protegidas retornam erro `401` para usuários não autenticados.
- APIs protegidas retornam erro `403` para usuários sem permissão.
- O administrador não pode inativar o próprio usuário logado pela tela de gestão.
- O administrador não pode remover o próprio perfil de administrador durante edição.

---

## [0.1.1] - Versão anterior

### Adicionado

- Cadastro de alunos com tag RFID.
- Cadastro de professores.
- Gestão acadêmica de cursos, turmas e vínculo professor-turma.
- Gestão de ambientes monitorados.
- Gestão de leitores RFID.
- Registro RFID via API.
- Histórico real de movimentações.
- Dashboard com resumo do banco de dados.
- Mapa com ambientes e leitores reais.
- Estrutura inicial de banco com MySQL.
- Separação de rotas por Blueprints Flask.
- Arquivos `schema.sql` e `seed.sql`.

### Alterado

- Limpeza da versão 0.1.
- Remoção de arquivos de ambiente local da versão publicável.
- Padronização dos textos de versão.
- Remoção de referências antigas de protótipo visual.
- Organização dos arquivos auxiliares para instalação.

### Observações

- O login ainda era visual/local.
- As permissões ainda não estavam implementadas.
- As APIs ainda não tinham camada completa de autenticação.