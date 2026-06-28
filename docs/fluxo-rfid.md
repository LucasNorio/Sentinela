# Fluxo RFID

O fluxo RFID é o centro do Sentinela.

## Fluxo implementado na versão 0.1.2

```txt
1. Aluno é cadastrado no sistema.
2. Uma tag RFID é vinculada ao aluno.
3. Um ambiente é cadastrado.
4. Um leitor RFID é vinculado ao ambiente.
5. Uma leitura RFID é enviada para a API.
6. O sistema identifica tag, aluno, leitor e ambiente.
7. O sistema salva o registro no histórico.
8. O dashboard e o mapa passam a refletir os dados registrados.
```

## Endpoint principal

```txt
POST /api/registros-rfid
```

Exemplo de payload:

```json
{
  "codigo_tag_lida": "RFID-001A",
  "codigo_leitor": "RFID_LAB_01",
  "tipo": "Entrada",
  "observacao": "Teste manual"
}
```

## Tipos de registro

```txt
Entrada
Saída
Movimentação
Alerta
```

## Situações de alerta

O sistema registra alerta quando encontra inconsistências como:

- Tag não cadastrada.
- Tag inativa, bloqueada ou perdida.
- Aluno inativo.
- Leitor inativo ou em manutenção.
- Ambiente inativo ou em manutenção.

## Próxima evolução do fluxo

Na versão futura de chamada automática, o registro RFID deverá ser interpretado em relação a aulas, horários e turmas, gerando presença automática.
