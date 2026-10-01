Sentinela v0.4.0

Sistema de chamada automática e monitoramento escolar baseado em RFID.

O Sentinela é um projeto de TCC desenvolvido para auxiliar no controle de presença e no acompanhamento da movimentação de alunos em ambiente escolar.

A versão 0.4.0 amplia o núcleo de chamada automática com a integração física dos leitores RFID baseados em ESP32. A partir desta versão, o Sentinela passa a possuir comunicação entre os leitores físicos e o backend Flask, permitindo o envio automático das leituras RFID para processamento pelo sistema.

Além das funcionalidades acadêmicas, RFID e de autenticação desenvolvidas nas versões anteriores, a v0.4.0 mantém o gerenciamento de aulas, geração de chamadas, processamento de registros RFID, classificação automática de presença, correções manuais auditadas e controle de acesso de professores, adicionando a comunicação com leitores RFID físicos.

A integração física RFID foi adicionada nesta versão. Os leitores utilizam ESP32, MFRC522 e Wi-Fi para enviar as leituras ao backend Flask. Os testes físicos continuam sendo realizados em ambiente controlado.

Funcionalidades da versão 0.4.0

Chamada e presença escolar

Cadastro de aulas

Associação da aula com:

turma

professor

ambiente

data

horário

tolerância de atraso

Estados de aula:

Programada

Em andamento

Finalizada

Cancelada

Validação de conflitos de horário entre:

turmas

professores

ambientes

Geração de chamada para alunos ativos da turma

Proteção contra geração duplicada de presença

Início controlado da aula

Processamento de registros RFID

Classificação automática de alunos como:

Presente

Atrasado

Classificação automática como Ausente ao finalizar a chamada

Situações de presença:

Pendente

Presente

Atrasado

Ausente

Justificado

Correção manual de presença

Obrigatoriedade de motivo para correções

Histórico de ajustes de presença

Registro do usuário responsável pela correção

Cancelamento de aulas programadas com motivo

Preservação dos registros históricos de aulas canceladas

Regras de processamento RFID

Para que um registro RFID possa ser utilizado pela chamada, o sistema considera informações como:

aluno associado ao registro

ambiente da aula

horário da leitura

janela válida da aula

tolerância configurada

situação do aluno

situação da tag RFID

situação do leitor

situação do ambiente

tipo do registro RFID

Registros inválidos ou de alerta não são utilizados para confirmar presença.

Integração com hardware RFID

A versão 0.4.0 inclui o código de firmware dos leitores RFID físicos em:

arduino/sentinela_rfid/sentinela_rfid.ino

Os leitores utilizam:

ESP32

MFRC522

Wi-Fi

HTTP/JSON

LED verde

LED vermelho

buzzer

Cada leitor possui um código próprio, enquanto a estrutura do firmware permanece compartilhada entre os dispositivos.

O fluxo de comunicação é:

Tag RFID
   ↓
MFRC522
   ↓
ESP32
   ↓
Wi-Fi
   ↓
POST /api/leitores-rfid/bip
   ↓
Backend Flask
   ↓
Registro RFID
   ↓
Processamento da chamada
   ↓
Resposta JSON
   ↓
LED / buzzer do leitor

O leitor envia ao backend o código da tag e o código identificador do próprio leitor. A resposta do servidor é utilizada pelo ESP32 para indicar o resultado da operação.

Em caso de presença efetivamente registrada, o leitor aciona o LED verde e um sinal sonoro. Em situações de leitura inválida, falha de comunicação ou ausência de registro de presença, o leitor utiliza o LED vermelho e o sinal sonoro correspondente.

O código publicado no repositório não contém as credenciais reais da rede Wi-Fi nem o endereço IP real do servidor. Essas informações devem ser configuradas localmente antes do uso.

A integração física está documentada e incluída no projeto, mas os testes dependem de um ambiente com os ESP32, leitores MFRC522, rede Wi-Fi e servidor Flask acessíveis entre si.

Autenticação e controle de acesso

O sistema possui autenticação utilizando usuários armazenados no MySQL.

Recursos

Login pelo banco de dados

Senhas armazenadas com hash

Sessões Flask

Logout

Registro do último login

Proteção de páginas

Proteção de APIs

Gestão de usuários

Inativação e reativação de usuários

Redefinição de senha

Controle de acesso conforme o perfil

Perfis disponíveis

Administrador

Coordenação

Secretaria

Professor

O perfil Professor pode ser associado a um cadastro acadêmico de professor através de usuario.id_professor.

O acesso às chamadas é limitado às turmas nas quais o professor possui vínculo ativo como:

Professor

Auxiliar

Dessa forma, um professor não pode consultar ou operar chamadas pertencentes a turmas às quais não está vinculado.

Gestão acadêmica

O Sentinela possui uma estrutura acadêmica utilizada pelos módulos de monitoramento e chamada.

Recursos

Cadastro de cursos

Cadastro de turmas

Cadastro de alunos

Cadastro de professores

Vínculo entre professores e turmas

Funções de vínculo:

Responsável

Professor

Auxiliar

Inativação de registros sem exclusão física

Preservação de histórico acadêmico

RFID e monitoramento

Recursos disponíveis

Cadastro de tags RFID

Associação de tag a aluno

Cadastro de ambientes

Cadastro de leitores RFID

Associação de leitor a ambiente

Registro de leituras RFID pela API

Histórico de movimentações

Identificação de situações de alerta

Estados para tags, leitores e ambientes

Utilização dos registros RFID pelo módulo de chamada

Os registros RFID são armazenados como eventos independentes.

A interpretação desses eventos para determinar presença ocorre no módulo de chamada, mantendo separados:

Evento RFID bruto
        ↓
Registro no histórico
        ↓
Processamento da chamada
        ↓
Presente / Atrasado / Ausente

Essa separação permite preservar o evento original mesmo quando a situação de presença sofre uma correção posterior.

Ciclo de uma chamada

O fluxo principal da versão 0.4.0 é:

Aula Programada
      ↓
Gerar chamada
      ↓
Presenças criadas como Pendente
      ↓
Iniciar aula
      ↓
Aula Em andamento
      ↓
Processar registros RFID
      ↓
Presente / Atrasado
      ↓
Finalizar chamada
      ↓
Pendentes tornam-se Ausentes
      ↓
Aula Finalizada

Uma aula ainda Programada também pode ser cancelada.

Programada
    ↓
Cancelar aula
    ↓
Cancelada

Aulas Finalizadas e Canceladas são estados terminais para as operações normais da chamada.

Correções e auditoria

Uma presença pode ser corrigida manualmente por usuários autorizados.

Cada alteração gera um registro em ajuste_presenca contendo:

presença alterada

usuário responsável

status anterior

novo status

motivo

data e hora da alteração

Exemplo:

Ausente
   ↓
Correção manual
   ↓
Justificado

O estado atual da presença é atualizado, mas o histórico da alteração permanece disponível para auditoria.

Preservação de dados

O Sentinela foi desenvolvido priorizando a preservação de registros históricos.

Dados relevantes não devem ser apagados fisicamente durante a operação normal do sistema.

São utilizados mecanismos como:

status

inativação

cancelamento

encerramento

motivo da alteração

data da alteração

histórico de ajustes

As principais chaves estrangeiras utilizam ON DELETE RESTRICT, reduzindo o risco de remoções acidentais destruírem dados relacionados.

Tecnologias utilizadas

Backend

Python

Flask

MySQL

mysql-connector-python

python-dotenv

Werkzeug Security

Frontend

HTML

CSS

JavaScript

Bootstrap 5.3.3

Projeto

RFID

API REST

Controle de acesso baseado em perfil

Sessões Flask

Requisitos

Python 3.11 ou superior

MySQL

Navegador moderno

Git, opcional para versionamento

Estrutura principal do projeto

Sentinela/
│
├── app.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CHANGELOG.md
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   │
│   └── migrations/
│       └── v0.3.0_chamada.sql
│
├── docs/
│
├── routes/
│   ├── auth_routes.py
│   ├── alunos_routes.py
│   ├── professores_routes.py
│   ├── academico_routes.py
│   ├── ambientes_routes.py
│   ├── leitores_routes.py
│   ├── registros_routes.py
│   ├── dashboard_routes.py
│   ├── usuarios_routes.py
│   ├── aulas_routes.py
│   ├── chamadas_routes.py
│   └── presencas_routes.py
│
├── scripts/
│   └── criar_usuarios_iniciais.py
│
├── static/
│   ├── css/
│   ├── images/
│   └── js/
│
└── templates/
    ├── index.html
    ├── home.html
    ├── chamada.html
    ├── mapa.html
    ├── historico.html
    ├── cadastro-alunos.html
    ├── cadastro-professores.html
    ├── gestao-academica.html
    ├── gestao-ambientes.html
    ├── gestao-leitores.html
    ├── administracao.html
    ├── gestao-usuarios.html
    └── sobre.html

Instalação

1. Clone ou baixe o projeto

Entre na pasta do projeto pelo terminal.

2. Crie um ambiente virtual

No Windows:

python -m venv .venv

Ative o ambiente:

.venv\Scripts\activate

Caso o PowerShell bloqueie a execução do script de ativação:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Depois:

.venv\Scripts\activate

3. Instale as dependências

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

As principais dependências são:

flask
mysql-connector-python
python-dotenv

4. Configure as variáveis de ambiente

Crie um arquivo:

.env

na raiz do projeto.

Utilize .env.example como referência.

Exemplo:

FLASK_SECRET_KEY=sua_chave_secreta

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha_mysql
MYSQL_DATABASE=sentinela_db

O arquivo .env não deve ser publicado no repositório.

5. Crie o banco de dados

Para uma instalação nova da versão 0.4.0, execute:

database/schema.sql

O arquivo cria o banco:

sentinela_db

e toda a estrutura necessária.

6. Execute os dados iniciais

Depois do schema, execute:

database/seed.sql

O seed adiciona os dados institucionais básicos necessários para iniciar o desenvolvimento.

Dados de testes acadêmicos, alunos, turmas, aulas e registros RFID não são adicionados automaticamente.

7. Crie os usuários iniciais

Na raiz do projeto:

python scripts/criar_usuarios_iniciais.py

O script cria ou atualiza os usuários de desenvolvimento e estabelece o vínculo necessário para o usuário com perfil Professor.

As credenciais utilizadas pelo ambiente de desenvolvimento são exibidas pelo próprio script.

As credenciais padrão são destinadas apenas ao desenvolvimento e devem ser alteradas antes do uso do sistema em um ambiente real.

8. Execute a aplicação

python app.py

O Flask iniciará o servidor de desenvolvimento.

Abra no navegador:

http://127.0.0.1:5000

Atualização da v0.2.0 para a v0.4.0

Para bancos já existentes da versão 0.2.0, não utilize o schema.sql para tentar atualizar as tabelas existentes.

Utilize a migration:

database/migrations/v0.4.0_chamada.sql

Ela adiciona a estrutura necessária para a versão 0.4.0, incluindo:

vínculo entre usuário e professor

função Professor/Auxiliar

tabela de aulas

tabela de presenças

tabela de auditoria de correções

Antes de aplicar migrations em um banco com dados importantes, recomenda-se realizar backup.

Principais entidades do banco

curso
  ↓
turma
  ├── aluno
  │    └── tag_rfid
  │
  └── professor_turma
         ↑
     professor
         ↑
       usuario

ambiente
   ↓
leitor_rfid
   ↓
registro_rfid

turma + professor + ambiente
             ↓
            aula
             ↓
          presenca
             ↓
      ajuste_presenca

Endpoints principais da v0.4.0

Aulas

GET    /api/aulas
GET    /api/aulas/<id>
POST   /api/aulas
PUT    /api/aulas/<id>
PATCH  /api/aulas/<id>/iniciar
PATCH  /api/aulas/<id>/cancelar

A finalização da aula deve ocorrer pelo módulo de chamada.

Chamadas

GET   /api/chamadas/<id_aula>
POST  /api/chamadas/<id_aula>/gerar
POST  /api/chamadas/<id_aula>/processar
POST  /api/chamadas/<id_aula>/finalizar

Presenças

PATCH /api/presencas/<id_presenca>/corrigir
GET   /api/presencas/<id_presenca>/ajustes

Estado da integração RFID

A versão 0.4.0 adiciona a integração física entre os leitores RFID e o backend do Sentinela.

O software do leitor ESP32 realiza a leitura da tag, identifica o leitor, envia a leitura por HTTP para o backend e interpreta a resposta para controlar os indicadores físicos.

Portanto:

Cadastro de tags                     ✅
Cadastro de leitores                 ✅
Cadastro de ambientes                ✅
Registro RFID pela API               ✅
Histórico de eventos                 ✅
Processamento automático da chamada  ✅
Firmware dos leitores ESP32          ✅
Comunicação Wi-Fi com o backend     ✅
Envio de tag + leitor por HTTP      ✅
Indicação por LED e buzzer          ✅
Testes físicos em outra máquina      ⏳

A integração está incluída no código publicado. A validação final depende da execução do backend e dos leitores em um segundo ambiente de testes.

Histórico das versões

v0.1.x

Base funcional do Sentinela:

estrutura acadêmica

cadastro de alunos

cadastro de professores

tags RFID

leitores

ambientes

registros RFID

histórico de movimentações

v0.2.0

Autenticação e controle de acesso:

usuários

login

hash de senha

sessões Flask

perfis

permissões

proteção de páginas e APIs

gestão de usuários

v0.3.0

Chamada e presença escolar:

aulas

conflitos de horário

chamada

processamento RFID

presença automática

atraso

ausência automática

cancelamento

correções manuais

auditoria

vínculo entre usuário e professor

acesso de Professor e Auxiliar por turma

Roadmap

v0.4.0 — Integração RFID

Integração física dos leitores RFID:

firmware para ESP32

leitura de tags com MFRC522

comunicação Wi-Fi

envio HTTP/JSON para o backend

identificação individual dos leitores

tratamento de respostas do servidor

indicação de resultado por LED e buzzer

preparação para testes em ambiente controlado

v0.5.0 — Relatórios

Planejado:

relatórios de presença

relatórios de movimentação

filtros avançados

exportação de informações

indicadores acadêmicos

v1.0.0 — Versão final

Objetivo:

consolidação dos módulos

integração completa

revisão de segurança

documentação final

testes finais

preparação para apresentação do TCC

Observações

O Sentinela encontra-se em desenvolvimento.

A versão 0.4.0 representa uma etapa funcional do projeto, incluindo a integração entre software e hardware RFID, mas não deve ser considerada uma solução pronta para produção.

Relatórios avançados, testes ampliados e outras funcionalidades continuam previstas para versões posteriores.

Projeto acadêmico

Projeto desenvolvido como Trabalho de Conclusão de Curso na área de Desenvolvimento de Sistemas.