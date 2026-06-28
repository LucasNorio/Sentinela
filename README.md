# Sentinela v0.1.1

Sistema de chamada automática e monitoramento escolar por RFID.

A versão 0.1.1 é uma limpeza da versão 0.1: remove arquivos de ambiente local, padroniza textos de versão, remove referências antigas de protótipo e organiza arquivos auxiliares para instalação.

## Funcionalidades desta versão

- Cadastro de alunos com tag RFID
- Cadastro de professores
- Gestão acadêmica de cursos, turmas e vínculo professor-turma
- Gestão de ambientes monitorados
- Gestão de leitores RFID
- Registro RFID via API
- Histórico real de movimentações
- Dashboard com resumo do banco de dados
- Mapa com ambientes e leitores reais

## Requisitos

- Python 3.11 ou superior
- MySQL
- Navegador moderno

## Instalação

1. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie o banco de dados:

```sql
SOURCE database/schema.sql;
SOURCE database/seed.sql;
```

4. Crie o arquivo `.env` a partir do exemplo:

```bash
copy .env.example .env
```

No Linux/macOS:

```bash
cp .env.example .env
```

5. Edite o `.env` com a senha local do MySQL.

6. Inicie o Flask:

```bash
python app.py
```

7. Acesse:

```txt
http://127.0.0.1:5000
```

## Observações

- O login ainda é visual/local e deve ser substituído por autenticação real em versões futuras.
- Os registros RFID já são persistidos no MySQL.
- Dados importantes são inativados em vez de excluídos, preservando histórico.
- O arquivo `.env` real não deve ser versionado.

## Próximas versões sugeridas

- v0.2: autenticação real, sessões e perfis de acesso.
- v0.3: chamada automática com aulas, presença e correções de professor.
- v0.4: integração com hardware físico enviando leituras RFID.
- v0.5: relatórios, filtros avançados e exportações.
