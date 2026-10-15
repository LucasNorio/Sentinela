Sentinela v0.4.0 — Integração RFID Física e Controle de Presença

A versão 0.4.0 do Sentinela introduz o núcleo de chamada automática e controle de presença escolar do sistema.

A partir desta versão, o Sentinela passa a relacionar aulas, turmas, professores, ambientes, alunos e registros RFID para determinar a situação de presença de cada aluno.

Além da autenticação, controle de acesso e estrutura acadêmica desenvolvidos nas versões anteriores, a v0.4.0 adiciona gerenciamento de aulas, geração de chamadas, processamento de registros RFID, classificação automática de presença, correções manuais auditadas e controle de acesso de professores conforme seus vínculos acadêmicos.

A versão 0.4.0 adiciona a integração física com leitores RFID baseados em ESP32 e MFRC522. Os leitores comunicam-se com o backend Flask através da rede Wi-Fi e enviam as leituras para a API do Sentinela.

Destaques da versão

Cadastro e gerenciamento de aulas

Geração automática de chamadas

Processamento de registros RFID

Classificação automática de presença

Identificação de atrasos

Geração automática de ausência

Correções manuais de presença

Auditoria das correções

Cancelamento de aulas

Validação de conflitos de horários

Controle de acesso de professores por turma

Suporte a professores vinculados como Auxiliar

Integração entre usuário e cadastro acadêmico de professor

Nova tela de Chamada

Novas APIs de aulas, chamadas e presenças

Atualização do banco de dados

Migration da v0.2.0 para a v0.4.0

Integração física com leitores RFID ESP32

Leitor MFRC522 conectado ao ESP32

Comunicação dos leitores através de Wi-Fi

Identificação individual de cada leitor

Envio de UID e código do leitor via HTTP/JSON

Feedback local por LED verde, LED vermelho e buzzer

Firmware do leitor incluído no repositório

Chamada automática

A principal funcionalidade adicionada nesta versão é o módulo de chamada.

Uma aula é associada a:

turma;

professor;

ambiente;

data;

horário de início;

horário de término;

tolerância de atraso.

O fluxo principal funciona da seguinte forma:

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

Aulas ainda programadas também podem ser canceladas:

Programada
    ↓
Cancelar
    ↓
Cancelada

Estados da aula

A versão 0.4.0 trabalha com quatro estados principais.

Programada

A aula ainda não foi iniciada.

Permite:

edição;

geração da chamada;

início da aula após a chamada ser gerada;

cancelamento.

Em andamento

A chamada está ativa.

Permite:

processamento de registros RFID;

atualização da chamada;

finalização da chamada.

A aula não pode mais ser editada ou cancelada.

Finalizada

A chamada foi encerrada.

Presenças que permaneciam como Pendente são automaticamente convertidas para Ausente.

A aula permanece disponível para consulta e correções de presença autorizadas.

Cancelada

A aula foi cancelada antes de seu início.

O sistema registra:

data do cancelamento;

motivo do cancelamento.

Registros já existentes são preservados para histórico.

Situações de presença

Cada aluno possui uma situação individual na chamada.

Os estados disponíveis são:

Pendente

Presente

Atrasado

Ausente

Justificado

Pendente

Estado inicial após a geração da chamada.

Presente

Pode ser identificado automaticamente por um registro RFID válido dentro da janela de presença.

Atrasado

Utilizado quando o registro RFID válido ocorre após o limite de tolerância configurado para a aula.

Ausente

Gerado automaticamente quando uma chamada é finalizada e o aluno ainda está como Pendente.

Justificado

Pode ser utilizado através de correção manual por um usuário autorizado.

Processamento RFID

Os registros RFID continuam sendo armazenados como eventos independentes.

A presença não substitui nem altera o registro RFID original.

O fluxo é:

Leitura RFID
    ↓
Registro RFID bruto
    ↓
Histórico
    ↓
Processamento da chamada
    ↓
Presente / Atrasado

Para que um registro possa ser utilizado na chamada, o sistema considera fatores como:

aluno relacionado;

ambiente da aula;

horário da leitura;

janela válida da aula;

tolerância;

estado do aluno;

estado da tag;

estado do leitor;

estado do ambiente;

tipo do registro RFID.

Registros classificados como Alerta não são utilizados para confirmar presença.

Integração RFID física

A versão 0.4.0 conecta o fluxo de presença do Sentinela a leitores RFID físicos baseados em ESP32.

Cada leitor utiliza:

ESP32;

módulo RFID MFRC522;

comunicação Wi-Fi;

LED verde;

LED vermelho;

buzzer.

O firmware dos leitores está versionado em:

arduino/sentinela_rfid/sentinela_rfid.ino

Os leitores utilizam essencialmente o mesmo firmware, diferenciando-se pelo código de identificação configurado em cada dispositivo.

O fluxo físico é:

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
Presença

A requisição enviada pelo ESP32 contém o UID da tag e a identificação do leitor:

{
  "codigo_tag": "UID_DA_TAG",
  "codigo_leitor": "LEITOR-01"
}

O endereço do servidor deve ser configurado no firmware de acordo com a máquina que estiver executando o backend.

Informações específicas da rede de desenvolvimento, como SSID, senha e endereço IP local, não devem ser utilizadas na versão pública do firmware. O código disponibilizado no repositório utiliza valores de exemplo.

Feedback do leitor

O leitor fornece feedback local de acordo com o resultado recebido do backend.

Presença registrada

Quando o backend confirma uma presença válida:

LED verde é acionado;

LED vermelho permanece desligado;

buzzer emite um sinal curto.

Presença não registrada

Quando a leitura não resulta em presença:

LED verde permanece desligado;

LED vermelho é acionado;

buzzer emite um sinal de erro.

Erro de comunicação

Quando o ESP32 não consegue comunicar-se com o backend ou está desconectado do Wi-Fi:

LED verde permanece desligado;

LED vermelho é acionado;

buzzer sinaliza o erro.

O firmware também registra no monitor serial o UID lido, o leitor utilizado, o tempo da requisição HTTP, o código HTTP retornado e a resposta do servidor.

Relação entre leitor e ambiente

O código do leitor identifica fisicamente qual dispositivo realizou a leitura. O backend utiliza essa informação juntamente com o ambiente associado ao leitor para determinar se a leitura pode participar da chamada em andamento.

Assim, uma tag válida não é suficiente, por si só, para confirmar presença: a leitura também precisa estar relacionada ao contexto correto da aula.

Estado atual da integração

A estrutura de software e o firmware dos leitores estão versionados nesta release.

Os testes físicos dos leitores RFID dependem da execução do backend em uma máquina acessível pela mesma rede Wi-Fi utilizada pelos ESP32. A validação final do fluxo completo deverá ser realizada em uma segunda máquina com o projeto instalado e com os leitores configurados para apontar para o endereço do servidor dessa máquina.

Validação de horários

A criação e edição de aulas passou a validar conflitos.

O sistema bloqueia sobreposição de horário quando existe outra aula com:

a mesma turma;

o mesmo professor;

o mesmo ambiente.

Aulas canceladas não bloqueiam o horário.

Horários adjacentes são permitidos.

Exemplo:

08:00 → 09:00
09:00 → 10:00

Não é considerado conflito.

Professores e turmas

A versão 0.4.0 adiciona uma associação entre:

usuario
   ↓
id_professor
   ↓
professor
   ↓
professor_turma
   ↓
turma

Um usuário com perfil Professor precisa estar associado a um cadastro acadêmico de professor.

O acesso às chamadas é determinado pelos vínculos ativos na tabela professor_turma.

São aceitas as funções:

Professor

Auxiliar

Dessa forma, um professor pode acessar somente as chamadas das turmas às quais possui vínculo ativo.

Auxiliar

Professores vinculados a uma turma como Auxiliar também podem operar a chamada daquela turma.

Isso permite que mais de um professor autorizado acompanhe e gerencie a presença sem remover a identificação do professor principal da aula.

Correções de presença

A versão 0.4.0 permite correções manuais de presença.

Usuários autorizados podem alterar uma situação como:

Ausente
   ↓
Justificado

ou:

Atrasado
   ↓
Presente

Toda correção exige um motivo.

Não é permitido realizar uma correção quando o novo estado é igual ao estado atual.

Auditoria

Cada correção manual gera um registro na tabela:

ajuste_presenca

São armazenados:

presença alterada;

usuário responsável;

status anterior;

novo status;

motivo;

data e hora da alteração.

O histórico pode ser consultado posteriormente pela interface.

Isso permite preservar a rastreabilidade das alterações realizadas na chamada.

Cancelamento de aulas

Aulas programadas podem ser canceladas.

O cancelamento exige um motivo.

O sistema registra:

cancelada_em
motivo_cancelamento

Uma aula:

Em andamento

Finalizada

já Cancelada

não pode ser cancelada novamente.

Aulas canceladas deixam de participar da validação de conflitos de horário.

Segurança e controle de acesso

A camada de autenticação introduzida na v0.2.0 continua sendo utilizada.

A v0.4.0 adiciona validações específicas para o módulo de chamada.

Principais regras:

usuários não autenticados recebem 401;

usuários sem permissão recebem 403;

professores não podem acessar chamadas de turmas sem vínculo;

o backend valida o acesso independentemente da interface;

aulas em andamento não podem ser editadas;

aulas finalizadas não podem retornar ao fluxo operacional;

aulas canceladas não podem ser operadas;

correções em aulas canceladas são bloqueadas;

correções em aulas ainda programadas são bloqueadas.

Perfis

Administrador

Possui acesso geral ao sistema.

Pode consultar e administrar os módulos conforme as regras globais de segurança.

Coordenação

Possui acesso aos módulos acadêmicos e ao módulo de chamada.

Pode:

criar aulas;

editar aulas programadas;

cancelar aulas;

iniciar aulas;

operar chamadas;

corrigir presenças;

consultar auditoria.

Secretaria

Possui acesso às áreas de cadastro e gestão acadêmica definidas pelo sistema.

Não opera o módulo de chamada na configuração atual da v0.4.0.

Professor

Possui acesso ao módulo de chamada somente nas turmas em que possui vínculo acadêmico ativo como:

Professor;

Auxiliar.

Pode:

visualizar aulas permitidas;

gerar chamadas;

iniciar aulas;

processar registros RFID;

finalizar chamadas;

corrigir presenças autorizadas;

consultar histórico de correções.

Não possui acesso à gestão administrativa geral.

Banco de dados

A versão 0.4.0 adiciona três entidades principais.

aula

Responsável pelo planejamento e estado de uma aula.

Campos principais:

id_aula
id_turma
id_professor
id_ambiente
data_aula
horario_inicio
horario_fim
tolerancia_minutos
status
criado_em
atualizado_em
cancelada_em
motivo_cancelamento

presenca

Relaciona um aluno a uma aula.

Campos principais:

id_presenca
id_aula
id_aluno
id_registro_rfid
status
origem
horario_detectado
observacao
criado_em
atualizado_em

Existe uma restrição única entre:

id_aula + id_aluno

evitando duplicação da presença de um mesmo aluno na mesma aula.

ajuste_presenca

Armazena a trilha de auditoria das correções.

Campos principais:

id_ajuste_presenca
id_presenca
id_usuario
status_anterior
status_novo
motivo
criado_em

Alterações na tabela usuario

Foi adicionado:

id_professor

O campo permite relacionar uma conta de usuário com um cadastro acadêmico de professor.

Esse vínculo é utilizado para determinar quais turmas e chamadas podem ser acessadas.

Novas APIs

Aulas

GET    /api/aulas
GET    /api/aulas/<id>
POST   /api/aulas
PUT    /api/aulas/<id>
PATCH  /api/aulas/<id>/iniciar
PATCH  /api/aulas/<id>/cancelar

Chamadas

GET   /api/chamadas/<id_aula>
POST  /api/chamadas/<id_aula>/gerar
POST  /api/chamadas/<id_aula>/processar
POST  /api/chamadas/<id_aula>/finalizar

Presenças

PATCH /api/presencas/<id_presenca>/corrigir
GET   /api/presencas/<id_presenca>/ajustes

Migration

Para bancos já existentes na v0.2.0 foi criada a migration da v0.4.0:

database/migrations/v0.4.0_chamada.sql

Ela adiciona:

usuario.id_professor;

função do vínculo professor-turma;

tabela aula;

tabela presenca;

tabela ajuste_presenca;

índices e chaves estrangeiras necessárias.

Para instalações novas deve ser utilizado diretamente:

database/schema.sql

Instalação

Fluxo recomendado para uma instalação nova:

1. Criar e ativar o ambiente virtual
2. Instalar requirements.txt
3. Criar o arquivo .env
4. Executar database/schema.sql
5. Executar database/seed.sql
6. Executar scripts/criar_usuarios_iniciais.py
7. Executar app.py

No terminal:

python -m pip install -r requirements.txt
python scripts/criar_usuarios_iniciais.py
python app.py

Testes realizados

A versão 0.4.0 passou por testes funcionais e de integridade do backend, banco de dados e fluxo de chamada envolvendo:

geração repetida da mesma chamada;

início repetido da mesma aula;

processamento repetido sem novas leituras;

presença corrigida para o mesmo status;

RFID em ambiente incorreto;

RFID fora da janela de horário;

aluno incluído após geração da chamada;

aluno inativado após geração da presença;

leitura RFID de aluno inativo;

tag RFID bloqueada;

leitor em manutenção;

ambiente em manutenção;

aula finalizada;

aula cancelada;

classificação como Presente;

classificação como Atrasado;

geração automática de Ausente;

correção de presença;

auditoria das correções;

conflito de turma;

conflito de professor;

conflito de ambiente;

horários adjacentes;

acesso de Professor por turma;

acesso de Auxiliar;

tentativa de Professor acessar outra turma;

edição de aula Em andamento pela API;

correção de presença em aula Programada.

Os testes físicos com os leitores ESP32/MFRC522 ainda dependem de uma máquina de execução do backend acessível pela mesma rede dos dispositivos. Por isso, a validação completa do fluxo físico fica registrada como teste de integração a ser executado após a instalação desta release em outra máquina.

Arquivos importantes adicionados

routes/aulas_routes.py
routes/chamadas_routes.py
routes/presencas_routes.py

templates/chamada.html

static/js/chamada.js

database/migrations/v0.4.0_chamada.sql

Arquivos atualizados

app.py

routes/auth_routes.py

database/schema.sql
database/seed.sql

scripts/criar_usuarios_iniciais.py

templates/sobre.html

README.md
CHANGELOG.md

Outros arquivos de interface e autenticação também podem ter recebido ajustes para integração com o novo módulo.

Limitações conhecidas

A versão 0.4.0 possui a integração física inicial com leitores RFID, mas ainda possui limitações:

os leitores dependem de uma rede Wi-Fi acessível ao computador que executa o backend;

o endereço do servidor precisa ser configurado no firmware de acordo com a máquina utilizada;

não há autenticação específica ou credencial criptográfica entre o ESP32 e a API;

a validação física completa em uma segunda máquina ainda precisa ser executada;

recuperação de senha por e-mail ainda não está disponível;

tabela dinâmica de permissões ainda não está disponível;

auditoria completa de todas as ações administrativas ainda não está disponível;

relatórios avançados ainda não estão disponíveis;

exportação CSV ainda não está disponível;

exportação PDF ainda não está disponível.

Essas funcionalidades permanecem planejadas para versões futuras.

Próximas etapas

v0.5.0 — Relatórios e exportações

Planejado:

relatórios por aluno;

relatórios por turma;

relatórios de presença;

relatórios de movimentação;

filtros avançados;

exportação CSV;

exportação PDF.

v1.0.0 — Versão final

Objetivo:

consolidar todos os módulos;

finalizar integração RFID;

revisar segurança;

finalizar documentação;

executar testes finais;

preparar o sistema para apresentação do TCC.

Status da release

A versão 0.4.0 está focada no núcleo de chamada automática e controle de presença.

Ela transforma os registros RFID, que anteriormente eram utilizados principalmente para monitoramento e histórico, em uma fonte de eventos capaz de alimentar o processo de presença escolar.

A camada de software necessária para aulas, chamadas, processamento RFID, presença, correções e auditoria está implementada.

A integração com o hardware RFID físico permanece como a principal etapa prevista para a versão 0.4.0.
