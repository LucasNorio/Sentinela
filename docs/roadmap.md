# Roadmap

Este roadmap organiza a evolução planejada do Sentinela após a versão 0.1.2.

## v0.1.2 — apresentação pública

Objetivo: tornar o repositório mais compreensível para quem acessar o GitHub.

Inclui:

- README completo.
- Documentação técnica inicial.
- Screenshots.
- Changelog.
- Release notes.

## v0.2.0 — autenticação real e permissões

Objetivo: substituir login visual/local por autenticação real.

Planejado:

- Tabela de usuários funcional.
- Senhas com hash.
- Sessões Flask.
- Logout real.
- Proteção das APIs.
- Perfis de acesso.

Perfis sugeridos:

```txt
Administrador
Coordenação
Secretaria
Professor
```

## v0.3.0 — chamada automática

Objetivo: transformar registros RFID em presença escolar.

Planejado:

- Tabela de aulas.
- Geração de chamada por turma.
- Status de presença por aluno.
- Origem da presença: RFID, professor, coordenação ou sistema.
- Correção manual pelo professor.
- Histórico de alterações.

## v0.4.0 — integração com hardware físico

Objetivo: conectar o Arduino/placa RFID ao backend.

Planejado:

- Endpoint específico para hardware.
- Token de identificação do dispositivo.
- Envio real de leituras RFID.
- Monitoramento de última comunicação dos leitores.

## v0.5.0 — relatórios e exportações

Objetivo: melhorar consulta e apresentação de dados.

Planejado:

- Relatório por aluno.
- Relatório por turma.
- Relatório por período.
- Relatório por ambiente.
- Exportação CSV/PDF.
- Filtros avançados.

## v1.0.0 — versão estável

Objetivo: consolidar o sistema como uma versão completa e apresentável.

Possíveis critérios:

- Autenticação real.
- Chamada automática funcional.
- Hardware integrado.
- Relatórios.
- Documentação completa.
- Testes essenciais.
