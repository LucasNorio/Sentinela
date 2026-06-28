# Visão geral do Sentinela

O **Sentinela** é um sistema web de chamada automática e monitoramento escolar por RFID.

A proposta é reduzir dependência de controle manual de presença e permitir que a escola acompanhe registros de movimentação de alunos em ambientes monitorados.

## Problema

Em uma instituição de ensino, controlar presença e movimentação manualmente pode gerar atrasos, falhas de registro e dificuldade de consulta posterior. O Sentinela propõe uma base digital para centralizar esses dados.

## Solução proposta

O sistema cadastra alunos, professores, turmas, ambientes e leitores RFID. Quando uma tag é lida por um leitor, o backend registra a movimentação e disponibiliza os dados no histórico, no dashboard e no mapa de ambientes.

## Estado atual

A versão 0.1.2 é um protótipo funcional integrado ao banco de dados. Ela já registra leituras RFID via API e exibe essas informações em telas administrativas.

## Módulos da versão 0.1.2

- Login visual.
- Dashboard.
- Cadastro de alunos.
- Cadastro de professores.
- Gestão acadêmica.
- Gestão de ambientes.
- Gestão de leitores RFID.
- Registro RFID por API.
- Histórico de movimentações.
- Mapa de ambientes monitorados.
- Administração.
- Sobre o sistema.

## Próximo grande objetivo

A próxima evolução técnica é implementar autenticação real, sessões e perfis de acesso.
