# Sentinela v0.2.0 — Autenticação e Controle de Acesso

A versão 0.2.0 do Sentinela consolida a camada de autenticação, usuários e permissões do sistema.

Esta versão transforma o login, que antes era apenas visual/local, em uma autenticação real integrada ao banco de dados MySQL. Também adiciona controle de sessão, proteção de páginas, proteção de APIs, perfis de acesso e uma área administrativa para gerenciamento de usuários.

## Destaques da versão

- Login real pelo banco de dados
- Senhas protegidas por hash
- Sessão Flask
- Logout funcional
- Proteção de páginas internas
- Proteção de APIs
- Controle de permissões por perfil
- Interface adaptada conforme o perfil do usuário
- Registro de último login
- Gestão de usuários pelo painel administrativo
- Atualização da página Sobre
- Atualização do README
- Atualização do schema do banco
- Script para criação de usuários iniciais

## Perfis disponíveis

A versão 0.2.0 trabalha com quatro perfis principais.

### Administrador

Possui acesso total ao sistema.

Pode acessar:

- Home
- Mapa
- Histórico
- Cadastro de alunos
- Cadastro de professores
- Gestão acadêmica
- Gestão de ambientes
- Gestão de leitores RFID
- Administração
- Gestão de usuários
- Sobre

### Coordenação

Possui acesso às áreas de gestão acadêmica e operacional.

Pode acessar áreas como:

- Home
- Mapa
- Histórico
- Cadastro de alunos
- Cadastro de professores
- Gestão acadêmica
- Gestão de ambientes
- Gestão de leitores RFID
- Sobre

Não possui acesso à Gestão de Usuários.

### Secretaria

Possui acesso às áreas de cadastro e gestão operacional.

Pode acessar áreas como:

- Home
- Mapa
- Histórico
- Cadastro de alunos
- Cadastro de professores
- Gestão acadêmica
- Gestão de ambientes
- Gestão de leitores RFID
- Sobre

Não possui acesso à Gestão de Usuários.

### Professor

Possui acesso limitado às áreas de consulta.

Pode acessar:

- Home
- Mapa
- Histórico
- Sobre

Não possui acesso a cadastros, gestão acadêmica, administração ou gestão de usuários.

## Gestão de usuários

Foi adicionada uma nova tela administrativa:

```txt
/gestao-usuarios

Nessa tela, o administrador pode:

Listar usuários
Criar usuários
Editar nome, e-mail e perfil
Inativar usuários
Reativar usuários
Redefinir senhas
Consultar o último login

Também foi adicionada a API:

GET   /api/usuarios
POST  /api/usuarios
PUT   /api/usuarios/<id>
PATCH /api/usuarios/<id>/inativar
PATCH /api/usuarios/<id>/reativar
PATCH /api/usuarios/<id>/resetar-senha

Todas essas rotas são restritas ao perfil Administrador.

Segurança

A versão 0.2.0 adiciona uma camada inicial de segurança ao Sentinela.

Principais pontos:

As senhas são salvas com hash.
Usuários inativos não conseguem realizar login.
Páginas internas exigem autenticação.
APIs internas exigem autenticação.
Rotas sensíveis exigem permissão adequada.
Usuários sem sessão recebem erro 401.
Usuários sem permissão recebem erro 403.
A interface oculta menus e cards incompatíveis com o perfil do usuário.
O administrador não pode inativar o próprio usuário logado.
O administrador não pode remover seu próprio perfil de administrador pela edição.
Banco de dados

A tabela usuario foi adicionada ao schema.sql.

Campos principais:

id_usuario
nome
email
senha_hash
perfil
status
criado_em
atualizado_em
ultimo_login
inativado_em
motivo_inativacao

A tabela permite controle de:

autenticação;
perfil;
status;
último login;
inativação lógica;
motivo de inativação.
Instalação atualizada

A instalação agora exige a criação dos usuários iniciais após a criação do banco.

Fluxo recomendado:

1. Criar e ativar o ambiente virtual
2. Instalar dependências
3. Criar e configurar o arquivo .env
4. Executar database/schema.sql
5. Executar database/seed.sql
6. Executar python scripts/criar_usuarios_iniciais.py
7. Executar python app.py

Credenciais de desenvolvimento:

Administrador: admin@sentinela.com / admin123
Coordenação: coordenacao@sentinela.com / coord123
Secretaria: secretaria@sentinela.com / sec123
Professor: professor@sentinela.com / prof123

Essas credenciais são apenas para desenvolvimento e demonstração.

Arquivos importantes adicionados
routes/auth_routes.py
routes/usuarios_routes.py
templates/gestao-usuarios.html
static/js/usuarios.js
scripts/criar_usuarios_iniciais.py
Arquivos atualizados
app.py
database/schema.sql
database/seed.sql
static/js/auth.js
static/css/style.css
templates/index.html
templates/home.html
templates/mapa.html
templates/administracao.html
templates/sobre.html
README.md
Limitações conhecidas
Ainda não há recuperação de senha por e-mail.
Ainda não há autenticação por token para hardware RFID.
Ainda não há tabela separada de permissões.
Ainda não há log detalhado de auditoria de todas as ações administrativas.
Ainda não há chamada automática baseada em aula e horário.
Ainda não há integração física final com Arduino ou leitor RFID real.
Ainda não há relatórios ou exportações em PDF/CSV.

Essas limitações estão previstas para versões futuras.

Próximas etapas sugeridas
v0.3.0 — Chamada automática

Implementar:

cadastro de aulas;
registro de presença por aluno;
cálculo automático de presença com base nos registros RFID;
correções manuais pelo professor;
trilha de auditoria das alterações de chamada.
v0.4.0 — Integração com hardware RFID real

Implementar:

endpoint específico para hardware;
autenticação do dispositivo;
envio de leituras RFID por microcontrolador;
validação de leitores físicos;
testes com Arduino UNO R4 WiFi ou hardware equivalente.
v0.5.0 — Relatórios e exportações

Implementar:

relatórios por aluno;
relatórios por turma;
relatórios por ambiente;
filtros avançados por período;
exportação CSV;
exportação PDF.
Status da release

A versão 0.2.0 está focada em autenticação e controle de acesso.

Ela estabelece uma base mais segura e organizada para que as próximas versões avancem para a chamada automática e integração com hardware RFID real.