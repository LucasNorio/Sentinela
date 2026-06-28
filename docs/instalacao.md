# Instalação local

Este guia resume a instalação local da versão 0.1.2.

## Requisitos

- Python 3.11 ou superior.
- MySQL instalado e rodando.
- Git.
- Navegador moderno.

## Passo 1 — Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO
```

## Passo 2 — Criar ambiente virtual

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Passo 3 — Instalar dependências

```bash
pip install -r requirements.txt
```

## Passo 4 — Criar banco de dados

No MySQL:

```sql
SOURCE database/schema.sql;
SOURCE database/seed.sql;
```

## Passo 5 — Configurar `.env`

Copie:

```bash
cp .env.example .env
```

No Windows:

```bash
copy .env.example .env
```

Edite as credenciais do MySQL no arquivo `.env`.

## Passo 6 — Rodar aplicação

```bash
python app.py
```

Acesse:

```txt
http://127.0.0.1:5000
```

## Observação

Não envie o arquivo `.env` real para o GitHub.
