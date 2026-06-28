# Arquitetura inicial

A versão 0.1.2 utiliza uma arquitetura simples baseada em Flask, templates HTML, JavaScript puro e MySQL.

## Camadas principais

```txt
Navegador
↓
Templates HTML + CSS + JavaScript
↓
Rotas Flask
↓
MySQL
```

## Backend

O backend é feito com Flask e organizado em Blueprints por domínio.

Principais arquivos:

```txt
app.py                  Inicialização da aplicação e rotas de páginas
database.py             Conexão com MySQL
config.py               Leitura das variáveis de ambiente
routes/                 APIs por domínio
```

Principais Blueprints:

```txt
alunos_routes.py        Alunos e tags RFID
professores_routes.py   Professores
academico_routes.py     Cursos, turmas e vínculos professor-turma
ambientes_routes.py     Ambientes físicos
leitores_routes.py      Leitores RFID
registros_routes.py     Registros RFID
dashboard_routes.py     Resumo para dashboard e administração
```

## Frontend

O frontend utiliza templates HTML com Bootstrap, CSS próprio e JavaScript para consumir as APIs.

Principais pastas:

```txt
templates/              Páginas renderizadas pelo Flask
static/css/style.css    Estilos principais
static/js/              Scripts específicos por página
```

## Banco de dados

O banco utiliza MySQL. Os scripts iniciais estão em:

```txt
database/schema.sql
database/seed.sql
```

## Decisão de preservação histórica

O sistema evita exclusão física de dados importantes. O padrão usado é inativar, reativar ou colocar em manutenção, preservando registros históricos.

Isso é importante porque registros RFID e dados acadêmicos podem ser usados para auditoria e consulta futura.

## Limitação arquitetural atual

A versão 0.1.2 ainda mistura muita lógica diretamente nas rotas Flask. Para versões futuras, pode ser interessante separar:

```txt
routes/       Entrada HTTP
services/     Regras de negócio
repositories/ Acesso ao banco
models/       Representação das entidades
```
