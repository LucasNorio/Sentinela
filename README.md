# Sentinela v0.2.0

Sistema de chamada automática e monitoramento escolar por RFID.

A versão 0.2.0 consolida a camada de autenticação, usuários e permissões do Sentinela. Além da base funcional da versão anterior, o sistema agora possui login real pelo banco de dados, senhas protegidas por hash, sessão Flask, controle de acesso por perfil, proteção de páginas, proteção de APIs e gestão administrativa de usuários.

## Objetivo do projeto

O Sentinela tem como objetivo apoiar instituições de ensino no controle de presença, movimentação e monitoramento de alunos por meio de tecnologia RFID.

A proposta do sistema é registrar eventos de entrada, saída e movimentação em ambientes monitorados, permitindo que secretaria, coordenação, professores e equipe administrativa acompanhem as informações de forma organizada.

A versão atual ainda não representa a chamada automática completa, mas estabelece a base necessária para essa funcionalidade nas próximas versões.

## Funcionalidades da versão 0.2.0

- Login real com dados armazenados no MySQL
- Senhas armazenadas com hash
- Sessão Flask para usuários autenticados
- Logout funcional
- Proteção de páginas internas
- Proteção de APIs
- Perfis de acesso:
  - Administrador
  - Coordenação
  - Secretaria
  - Professor
- Controle visual de menus e cards conforme o perfil do usuário
- Registro de último login
- Gestão de usuários pelo painel administrativo
- Cadastro de alunos com vínculo de tag RFID
- Cadastro de professores
- Gestão acadêmica de cursos, turmas e vínculo professor-turma
- Gestão de ambientes monitorados
- Gestão de leitores RFID
- Registro RFID via API
- Histórico real de movimentações
- Dashboard com resumo do banco de dados
- Mapa com ambientes e leitores reais
- Inativação lógica de registros importantes, preservando histórico

## Requisitos

- Python 3.11 ou superior
- MySQL
- Navegador moderno
- Git, opcional para versionamento

## Tecnologias utilizadas

- Python
- Flask
- MySQL
- JavaScript
- HTML
- CSS
- Bootstrap
- Werkzeug Security
- RFID

## Instalação

### 1. Clone ou extraia o projeto

Acesse a pasta do projeto pelo terminal.

Exemplo:

```bash
cd caminho/para/Sentinela_v0.2
```

### 2. Crie e ative um ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Se o comando `python` não funcionar, use:

```bash
py -m venv .venv
.venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

Com o ambiente virtual ativado:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Crie o arquivo `.env`

Copie o arquivo de exemplo:

No Windows:

```bash
copy .env.example .env
```

No Linux/macOS:

```bash
cp .env.example .env
```

Depois edite o `.env` com as configurações locais do MySQL:

```env
FLASK_SECRET_KEY=sentinela_chave_de_desenvolvimento
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha_do_mysql
MYSQL_DATABASE=sentinela_db
```

O arquivo `.env` real não deve ser enviado para o GitHub.

### 5. Crie o banco de dados

Execute o arquivo:

```txt
database/schema.sql
```

Depois execute:

```txt
database/seed.sql
```

No MySQL Workbench, abra cada arquivo SQL e execute o conteúdo.

No terminal do MySQL, é possível usar:

```sql
SOURCE database/schema.sql;
SOURCE database/seed.sql;
```

### 6. Crie os usuários iniciais

Com o ambiente virtual ativado, rode:

```bash
python scripts/criar_usuarios_iniciais.py
```

Esse script cria ou atualiza os usuários iniciais de desenvolvimento.

Credenciais padrão:

```txt
Administrador: admin@sentinela.com / admin123
Coordenação: coordenacao@sentinela.com / coord123
Secretaria: secretaria@sentinela.com / sec123
Professor: professor@sentinela.com / prof123
```

Essas credenciais são destinadas apenas para desenvolvimento e demonstração.

### 7. Inicie o sistema

```bash
python app.py
```

Acesse no navegador:

```txt
http://127.0.0.1:5000
```

## Controle de acesso

A versão 0.2.0 possui controle de acesso por perfil.

### Administrador

Possui acesso total ao sistema, incluindo:

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

Possui acesso às áreas de consulta, gestão acadêmica e gestão operacional.

Pode acessar:

- Home
- Mapa
- Histórico
- Cadastro de alunos
- Cadastro de professores
- Gestão acadêmica
- Gestão de ambientes
- Gestão de leitores RFID
- Sobre

Não acessa:

- Gestão de usuários
- Recursos administrativos exclusivos do administrador

### Secretaria

Possui acesso às áreas de cadastro e gestão operacional.

Pode acessar:

- Home
- Mapa
- Histórico
- Cadastro de alunos
- Cadastro de professores
- Gestão acadêmica
- Gestão de ambientes
- Gestão de leitores RFID
- Sobre

Não acessa:

- Gestão de usuários
- Recursos administrativos exclusivos do administrador

### Professor

Possui acesso limitado às áreas de consulta.

Pode acessar:

- Home
- Mapa
- Histórico
- Sobre

Não acessa:

- Cadastro de alunos
- Cadastro de professores
- Gestão acadêmica
- Gestão de ambientes
- Gestão de leitores RFID
- Administração
- Gestão de usuários

## Estrutura principal do projeto

```txt
app.py
config.py
database.py
requirements.txt
.env.example
.gitignore
README.md
CHANGELOG.md
RELEASE_NOTES_v0.2.0.md

database/
  schema.sql
  seed.sql

scripts/
  criar_usuarios_iniciais.py

routes/
  auth_routes.py
  usuarios_routes.py
  alunos_routes.py
  professores_routes.py
  academico_routes.py
  ambientes_routes.py
  leitores_routes.py
  registros_routes.py
  dashboard_routes.py

templates/
  index.html
  home.html
  cadastro-alunos.html
  cadastro-professores.html
  gestao-academica.html
  gestao-ambientes.html
  gestao-leitores.html
  gestao-usuarios.html
  historico.html
  mapa.html
  administracao.html
  sobre.html

static/
  css/
    style.css
  js/
    auth.js
    usuarios.js
    alunos.js
    professores.js
    academico.js
    ambientes.js
    leitores.js
    historico.js
    mapa.js
    administracao.js
  images/
    logo/
      SENTINELALOGOtransparente.png
```

## Banco de dados

O banco principal do projeto é:

```txt
sentinela_db
```

Principais tabelas:

- `usuario`
- `curso`
- `turma`
- `aluno`
- `tag_rfid`
- `professor`
- `professor_turma`
- `ambiente`
- `leitor_rfid`
- `registro_rfid`

A tabela `usuario` foi adicionada e consolidada na versão 0.2.0 para suportar autenticação, perfis e controle de acesso.

## APIs principais

### Autenticação

```txt
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### Usuários

```txt
GET   /api/usuarios
POST  /api/usuarios
PUT   /api/usuarios/<id>
PATCH /api/usuarios/<id>/inativar
PATCH /api/usuarios/<id>/reativar
PATCH /api/usuarios/<id>/resetar-senha
```

### Cadastros e gestão

```txt
GET    /api/alunos
POST   /api/alunos
PUT    /api/alunos/<id>
PATCH  /api/alunos/<id>/inativar
PATCH  /api/alunos/<id>/reativar

GET    /api/professores
POST   /api/professores
PUT    /api/professores/<id>
PATCH  /api/professores/<id>/inativar
PATCH  /api/professores/<id>/reativar

GET    /api/cursos
POST   /api/cursos
PUT    /api/cursos/<id>
PATCH  /api/cursos/<id>/inativar
PATCH  /api/cursos/<id>/reativar

GET    /api/turmas
POST   /api/turmas
PUT    /api/turmas/<id>
PATCH  /api/turmas/<id>/inativar
PATCH  /api/turmas/<id>/reativar
PATCH  /api/turmas/<id>/encerrar

GET    /api/ambientes
POST   /api/ambientes
PUT    /api/ambientes/<id>
PATCH  /api/ambientes/<id>/inativar
PATCH  /api/ambientes/<id>/reativar
PATCH  /api/ambientes/<id>/manutencao

GET    /api/leitores-rfid
POST   /api/leitores-rfid
PUT    /api/leitores-rfid/<id>
PATCH  /api/leitores-rfid/<id>/inativar
PATCH  /api/leitores-rfid/<id>/reativar
PATCH  /api/leitores-rfid/<id>/manutencao
```

### RFID e dashboard

```txt
GET  /api/registros-rfid
POST /api/registros-rfid

GET /api/dashboard/resumo
GET /api/status
```

## Observações de segurança

- O login não é mais apenas visual ou local.
- A autenticação agora consulta a tabela `usuario`.
- As senhas são armazenadas com hash.
- As páginas internas exigem sessão autenticada.
- As APIs internas exigem autenticação.
- As permissões são aplicadas no backend.
- A interface também oculta menus e cards conforme o perfil.
- O arquivo `.env` não deve ser versionado.
- A pasta `.venv` não deve ser versionada.
- Arquivos de cache, como `__pycache__`, não devem ser enviados ao repositório.

## Arquivos que não devem ser publicados

Antes de publicar, verifique se estes itens não estão no projeto publicável:

```txt
.env
.venv/
venv/
__pycache__/
routes/__pycache__/
scripts/__pycache__/
node_modules/
.git/
package.json
package-lock.json
criar_admin.py
criar_usuarios_teste.py
*.pyc
```

## Status da versão

A versão 0.2.0 representa a consolidação do módulo de autenticação e controle de acesso do Sentinela.

Ela prepara o sistema para as próximas etapas do projeto, especialmente a implementação da chamada automática e a futura integração com hardware RFID real.

## Próximas versões sugeridas

- v0.3.0: chamada automática com aulas, presença e correções de professor.
- v0.4.0: integração com hardware físico enviando leituras RFID.
- v0.5.0: relatórios, filtros avançados e exportações.
- v1.0.0: versão final consolidada para apresentação do TCC.