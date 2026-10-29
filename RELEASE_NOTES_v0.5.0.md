# Sentinela v0.5.0 — Relatórios Acadêmicos

**Versão:** 0.5.0  
**Preparação:** 22 de outubro de 2026  
**Base:** v0.4.1 (codificação e cadastro de leitores RFID corrigidos)

## Objetivo

Entregar documentos acadêmicos de frequência utilizando as chamadas já registradas no Sentinela, sem transformar a v0.5.0 em um dashboard de análise.

## Novidades

1. **Relatório de frequência por turma:** escolha de turma e período, indicadores de aulas finalizadas, relação de alunos e resumo de presenças, atrasos, faltas, justificativas, cobertura e percentual quando conclusivo.
2. **Relatório individual do aluno:** identificação e resumo do aluno, tabela cronológica com aulas finalizadas, situação e origem dos registros, incluindo histórico com várias páginas.
3. **PDF para visualização, download e impressão:** formatação institucional, avisos de conferência, legenda, assinatura e paginação refinada.
4. **Controle de integridade:** percentual `N/D` quando há menos registros que aulas finalizadas; pendências em aulas finalizadas impedem emissão; não são inventadas faltas em lacunas de histórico.
5. **Testes automatizados:** 22 testes de consultas, autorização, regras de frequência, formatação e paginação do PDF com dados simulados.

## Alterações técnicas

- Novo blueprint `routes/relatorios_routes.py`, registrado no `app.py`.
- Nova página `templates/relatorios.html` e lógica de interface `static/js/relatorios.js`.
- Dependência `reportlab` para geração de PDFs.
- Testes em `tests/test_relatorios.py` e `tests/test_relatorio_individual.py`.
- Documentação e configuração de publicação revisadas; arquivo `.env.example` disponível.
- No pacote publicável: servidor Flask usa por padrão `127.0.0.1` sem debug; a configuração da rede para testes com ESP32 é explícita. O script de usuários iniciais deixa de usar senhas fixas.

## Compatibilidade e instalação

- **Banco v0.4.1 → v0.5.0:** nenhuma migration SQL necessária.
- Para instalação nova, execute `database/schema.sql` e `database/seed.sql` no MySQL.
- Atualize as dependências com `python -m pip install -r requirements.txt`.
- Copie `.env.example` para `.env`, configure credenciais locais e crie usuários iniciais com `python scripts/criar_usuarios_iniciais.py`.
- Para testes de hardware, configure `FLASK_HOST=0.0.0.0` somente em rede local protegida, com `FLASK_DEBUG=0`.

## Critérios dos relatórios

- Consideram somente aulas finalizadas no intervalo selecionado.
- Presentes e atrasados contam como comparecimento; justificativas não equivalem a presença.
- O cálculo percentual é fornecido apenas com cobertura completa das aulas finalizadas.
- Alunos que ingressaram após algumas aulas podem ter cobertura parcial; o banco ainda não registra toda a história de mudanças de turma.
- Professores têm acesso restrito a turmas com vínculo ativo, conforme a política implementada.

## Verificação

Os 22 testes automatizados foram executados com sucesso na etapa de preparação desta distribuição. O responsável pelo projeto também validou a emissão dos relatórios com MySQL local durante o desenvolvimento. **A publicação do pacote não constitui homologação para ambiente produtivo.**

## Fora do escopo

- Painéis com gráficos interativos e filtros analíticos avançados.
- Reconstrução retroativa do histórico de matrículas.
- Segurança e disponibilidade exigidas por implantação real de uma instituição escolar.

Consulte o `README.md` para instalação, endpoints e limitações e o `CHANGELOG.md` para o histórico das alterações.
