# Sentinela — v0.5.0

**Sistema acadêmico de monitoramento RFID, chamada automática e relatórios de frequência.**

O Sentinela é um projeto de TCC de Desenvolvimento de Sistemas. Ele relaciona alunos, turmas, professores, ambientes, aulas e leituras RFID para registrar presença e permitir acompanhamento acadêmico. É uma aplicação **em desenvolvimento, destinada a testes e demonstração**, não um produto homologado para uso em produção.

## Novidades da v0.5.0

- **Relatório de frequência por turma:** filtro por turma e período, prévia com presenças, atrasos, faltas, justificativas e cobertura de registros; visualização e download em PDF.
- **Relatório individual:** filtro por turma, aluno e período; histórico de aulas finalizadas com situação e origem dos registros; emissão em PDF.
- **Conferência de dados:** quando o aluno possui menos registros de presença do que aulas finalizadas, o percentual fica `N/D` e o documento sinaliza a necessidade de conferência. Ausências de registros não são convertidas automaticamente em faltas.
- **Paginação dos PDFs:** cabeçalho, tabela, notas, assinatura e rodapé distribuídos em páginas sem folhas extras desnecessárias em cenários testados.
- **Testes automatizados:** 22 testes de regras, acesso, PDFs e paginação, utilizando dados simulados (não exigem MySQL ativo).

A versão anterior, **v0.4.1**, corrigiu problemas de codificação UTF-8 e do cadastro de leitores RFID. A v0.5.0 não introduz alterações no esquema SQL em relação à v0.4.1.

## Principais funcionalidades

- Autenticação, sessões e perfis `Administrador`, `Coordenação`, `Secretaria` e `Professor`.
- Gestão acadêmica de cursos, turmas, alunos, professores e vínculos com turmas.
- Cadastro de ambientes, leitores e tags RFID, preservando eventos de leitura no histórico.
- Planejamento de aulas, controle de conflitos, geração, abertura e finalização de chamadas.
- Processamento de leituras RFID, classificação de presença/atraso e fechamento das pendências como ausências quando a chamada é finalizada.
- Correção manual de presença com motivo e trilha de auditoria.
- Consulta e emissão dos dois modelos de relatórios acadêmicos, com controle de acesso por perfil e vínculo com a turma.
- Firmware de referência para **ESP32 + MFRC522**, com comunicação HTTP/JSON via rede Wi-Fi.

> **Limites conhecidos:** não há histórico completo de ingresso e transferência de alunos entre turmas. Por isso, uma matrícula posterior à primeira aula pode gerar cobertura parcial e percentual `N/D`. A justificativa de ausência não é automaticamente computada como comparecimento. Os critérios precisam ser validados pela instituição antes de utilizar relatórios como documentos oficiais.

## Tecnologias

**Backend:** Python, Flask, MySQL, `mysql-connector-python`, `python-dotenv`, Werkzeug e ReportLab.

**Frontend:** HTML, CSS, JavaScript e Bootstrap 5.3.3 (via CDN).

**Hardware experimental:** ESP32, leitor RFID MFRC522, Wi-Fi, LEDs e buzzer.

## Pré-requisitos

- **Windows 10/11, macOS ou Linux** (exemplos de Linux para Ubuntu e Fedora).
- **Python 3.11 ou superior**, com suporte a ambientes virtuais (`venv`).
- **MySQL Server** instalado no computador ou acessível pela rede, com permissão para criar o banco inicialmente.
- Navegador moderno e acesso à Internet para instalar dependências; o Bootstrap é carregado por CDN.
- Para o leitor físico (opcional): ESP32, MFRC522 e rede local com conectividade ao servidor Flask.

### Preparar o Python e o MySQL no sistema operacional

**Windows**

Instale o Python 3.11+ pelo [site oficial](https://www.python.org/downloads/windows/) e o MySQL Server pelo [MySQL Installer](https://dev.mysql.com/downloads/installer/). Durante a instalação, configure uma senha para o usuário administrador do MySQL. Verifique no PowerShell:

```powershell
python --version
```

Se `python` não for reconhecido, tente `py -3 --version` e use `py -3` no lugar de `python` **antes de ativar** o ambiente virtual. Para importar o banco, você pode usar o MySQL Command Line Client ou o MySQL Workbench.

**macOS (Homebrew)**

Com o [Homebrew](https://brew.sh/) instalado, execute no Terminal:

```bash
brew install python mysql
brew services start mysql
python3 --version
mysql --version
```

A instalação do MySQL via Homebrew pode iniciar sem senha para o usuário `root` local. Configure a autenticação de acordo com o ambiente e não utilize o servidor sem proteção. Se o MySQL já estiver instalado por outro método, não é necessário reinstalá-lo.

**Linux — Ubuntu**

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip mysql-server
sudo systemctl enable --now mysql
python3 --version
mysql --version
```

**Linux — Fedora**

```bash
sudo dnf install python3 python3-pip mysql-server
sudo systemctl enable --now mysqld
python3 --version
mysql --version
```

Em outras distribuições, instale os pacotes equivalentes. Confira se a versão do Python é **3.11 ou superior**: o `python3` padrão de distribuições antigas pode ser anterior a essa versão. Os nomes dos pacotes e serviços MySQL também podem variar.

## Instalação local (Windows, macOS e Linux)

Todos os comandos a seguir devem ser executados **na pasta raiz do projeto**, onde estão `app.py` e `requirements.txt`.

### 1. Criar o ambiente virtual e instalar as dependências

**Windows — PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se a política do PowerShell bloquear a ativação, execute somente para a sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**macOS e Linux — Terminal (bash ou zsh):**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Em todos os sistemas, após a ativação do `.venv`, os comandos `python` e `python -m pip` utilizarão o ambiente virtual. Para desativá-lo mais tarde, execute `deactivate`.

### 2. Configurar as variáveis de ambiente

Copie o arquivo de exemplo para `.env`:

**Windows — PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS e Linux — Terminal:**

```bash
cp .env.example .env
```

Com o ambiente virtual ativo, gere uma chave secreta aleatória (igual nos três sistemas):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Abra `.env` no editor de sua preferência e cole o resultado em `FLASK_SECRET_KEY`. Ajuste também as variáveis:

```dotenv
FLASK_SECRET_KEY=cole_a_chave_gerada_aqui
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=0

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha_local_do_mysql
MYSQL_DATABASE=sentinela_db
```

As credenciais do exemplo são apenas orientativas. Para uso além de um ambiente local de desenvolvimento, prefira um usuário MySQL exclusivo para o Sentinela, com as permissões necessárias. **Nunca publique o `.env`.**

### 3. Preparar o banco de dados MySQL

Para um **banco novo**, importe nesta ordem:

1. `database/schema.sql` — cria `sentinela_db` e suas tabelas.
2. `database/seed.sql` — cadastra cursos de exemplo, sem criar alunos ou chamadas.

No MySQL Command Line Client ou no terminal, entre no cliente MySQL:

```bash
mysql -u root -p
```

Informe a senha configurada na instalação. Em instalações Linux com autenticação local por *socket*, pode ser necessário usar `sudo mysql` em vez do comando acima. No macOS, se a instalação inicial ainda não possuir senha para `root`, pode ser necessário utilizar `mysql -u root` e configurar uma senha antes de continuar.

No prompt do MySQL (`mysql>`), execute:

```sql
SOURCE database/schema.sql;
SOURCE database/seed.sql;
```

**Atenção:** o comando `SOURCE` assume que o cliente MySQL foi iniciado na raiz do projeto. Se não encontrar os arquivos, informe o caminho absoluto ou utilize o MySQL Workbench para abrir e executar os scripts na mesma ordem.

**Se você já tem o banco da v0.4.1, não execute o schema nem recrie o banco.** A v0.5.0 não requer migration SQL a partir da v0.4.1. O arquivo `database/migrations/v0.4.0_chamada.sql` é legado, voltado a bancos de versões anteriores; faça backup e confira a versão de origem antes de usá-lo.

### 4. Criar o usuário administrador inicial

No `.env`, configure uma senha forte, única, com pelo menos 12 caracteres:

```dotenv
SENTINELA_ADMIN_PASSWORD=substitua_por_uma_senha_forte_e_unica
```

Com o ambiente virtual ativo, execute **em qualquer um dos três sistemas operacionais**:

```bash
python scripts/criar_usuarios_iniciais.py
```

O script cria somente os perfis cujas variáveis `SENTINELA_*_PASSWORD` estejam configuradas, não imprime as senhas e **não redefine credenciais de usuários existentes**. Consulte `.env.example` para os perfis opcionais. Contas do perfil Professor devem ser vinculadas posteriormente ao cadastro acadêmico e às turmas autorizadas.

### 5. Iniciar o servidor

Com o ambiente virtual ativo:

```bash
python app.py
```

Abra no navegador: **http://127.0.0.1:5000**. Depois de autenticar, acesse `/chamada` ou `/relatorios`.

Se o servidor não conseguir iniciar, confirme se o MySQL está em execução, se o banco foi criado, se as credenciais em `.env` estão corretas e se a porta 5000 está livre.

### Acesso pela rede para testes com ESP32

Por padrão, o servidor inicia em `127.0.0.1`, sem depuração. Para permitir conexões de um ESP32 na mesma rede local, configure no `.env`:

```dotenv
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=0
```

Defina no firmware `arduino/sentinela_rfid/sentinela_rfid.ino` o SSID, a senha Wi-Fi, o endereço **LAN** do computador com Flask e o código do leitor cadastrado. A rede precisa permitir acesso à porta 5000 e estar protegida. **Não exponha o servidor de desenvolvimento, o depurador do Flask ou o endpoint HTTP do leitor à Internet.** A integração utiliza HTTP sem proteção de transporte e foi concebida para testes em ambiente controlado.

## Relatórios e regras de frequência

Na página `/relatorios`, os filtros aceitam datas no formato ISO (`AAAA-MM-DD`); o período deve ser válido e não pode ultrapassar 367 dias corridos.

- A contagem usa apenas aulas `Finalizada`.
- Status tratados: `Presente`, `Atrasado`, `Ausente`, `Justificado` e `Pendente`.
- A frequência é `(Presentes + Atrasados) / registros × 100`, **somente quando a cobertura das aulas finalizadas está completa**.
- `Justificado` integra o denominador, sem equivaler automaticamente a presença.
- Presenças `Pendente` em aulas finalizadas bloqueiam a emissão até regularização.
- Correções manuais realizadas depois da chamada são refletidas em novas consultas.
- Usuários com perfil Professor precisam de vínculo ativo `Professor` ou `Auxiliar` com a turma; outros perfis usam as políticas de acesso configuradas no sistema.

**Endpoints principais dos relatórios** (exigem sessão válida e autorização):

```text
GET /api/relatorios/turmas
GET /api/relatorios/turmas/<id_turma>/frequencia?inicio=AAAA-MM-DD&fim=AAAA-MM-DD
GET /api/relatorios/turmas/<id_turma>/frequencia.pdf?inicio=AAAA-MM-DD&fim=AAAA-MM-DD
GET /api/relatorios/turmas/<id_turma>/alunos
GET /api/relatorios/turmas/<id_turma>/alunos/<id_aluno>/frequencia?inicio=AAAA-MM-DD&fim=AAAA-MM-DD
GET /api/relatorios/turmas/<id_turma>/alunos/<id_aluno>/frequencia.pdf?inicio=AAAA-MM-DD&fim=AAAA-MM-DD
```

Nos endpoints `.pdf`, utilize `&download=1` para solicitar o arquivo como anexo.

## Testes

Com o ambiente virtual ativado no Windows, macOS ou Linux:

```bash
python -m unittest discover -s tests -v
```

A suíte atual possui **22 testes automatizados**, focados no módulo de relatórios e realizados com banco simulado. Ela não substitui a validação com MySQL real, as regras de outros módulos nem os testes físicos do ESP32. Os comandos de instalação para macOS e Linux devem ser confirmados no ambiente específico; o projeto ainda é experimental.

## Organização

```text
Sentinela/
├── app.py, config.py, database.py, requirements.txt
├── .env.example
├── arduino/sentinela_rfid/sentinela_rfid.ino
├── database/schema.sql, database/seed.sql, database/migrations/
├── routes/relatorios_routes.py   # outros blueprints em routes/
├── scripts/criar_usuarios_iniciais.py
├── static/css/, static/js/, static/images/
├── templates/relatorios.html     # demais páginas em templates/
├── tests/test_relatorios.py
├── tests/test_relatorio_individual.py
├── CHANGELOG.md
└── RELEASE_NOTES_v0.5.0.md
```

## Segurança, privacidade e uso acadêmico

- Não versione `.env`, senhas, backups de produção, bancos com dados pessoais nem ambientes virtuais.
- O script de usuários iniciais aceita senhas configuradas localmente; proteja essas variáveis e troque credenciais comprometidas.
- Os relatórios podem conter **dados pessoais de estudantes**; restrinja acesso, armazenamento, compartilhamento e impressão de acordo com a política da instituição e legislação aplicável.
- A aplicação utiliza o servidor de desenvolvimento Flask e comunicação HTTP no protótipo de IoT. São necessárias melhorias de implantação, autenticação do dispositivo e segurança de transporte para operação real.

O Sentinela é um **projeto acadêmico de TCC**, ainda em desenvolvimento. O dashboard gráfico interativo não integra o escopo da v0.5.0 e poderá ser avaliado em uma etapa posterior.
