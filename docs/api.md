# API da versão 0.1.2

Esta documentação resume os principais endpoints disponíveis na versão 0.1.2.

## Status e dashboard

```txt
GET /api/status
GET /api/dashboard/resumo
```

## Alunos

```txt
GET    /api/alunos
POST   /api/alunos
PUT    /api/alunos/<id>
PATCH  /api/alunos/<id>/inativar
PATCH  /api/alunos/<id>/reativar
```

## Professores

```txt
GET    /api/professores
POST   /api/professores
PUT    /api/professores/<id>
PATCH  /api/professores/<id>/inativar
PATCH  /api/professores/<id>/reativar
```

## Cursos

```txt
GET    /api/cursos
POST   /api/cursos
PUT    /api/cursos/<id>
PATCH  /api/cursos/<id>/inativar
PATCH  /api/cursos/<id>/reativar
```

## Turmas

```txt
GET    /api/turmas
POST   /api/turmas
PUT    /api/turmas/<id>
PATCH  /api/turmas/<id>/inativar
PATCH  /api/turmas/<id>/reativar
PATCH  /api/turmas/<id>/encerrar
```

## Vínculo professor-turma

```txt
GET    /api/professor-turma
POST   /api/professor-turma
PUT    /api/professor-turma/<id>
PATCH  /api/professor-turma/<id>/inativar
PATCH  /api/professor-turma/<id>/reativar
```

## Ambientes

```txt
GET    /api/ambientes
POST   /api/ambientes
PUT    /api/ambientes/<id>
PATCH  /api/ambientes/<id>/inativar
PATCH  /api/ambientes/<id>/reativar
PATCH  /api/ambientes/<id>/manutencao
```

## Leitores RFID

```txt
GET    /api/leitores-rfid
POST   /api/leitores-rfid
PUT    /api/leitores-rfid/<id>
PATCH  /api/leitores-rfid/<id>/inativar
PATCH  /api/leitores-rfid/<id>/reativar
PATCH  /api/leitores-rfid/<id>/manutencao
```

## Registros RFID

```txt
GET    /api/registros-rfid
POST   /api/registros-rfid
```

Exemplo de POST:

```json
{
  "codigo_tag_lida": "RFID-001A",
  "codigo_leitor": "RFID_LAB_01",
  "tipo": "Entrada",
  "observacao": "Teste manual"
}
```

## Observação sobre autenticação

A versão 0.1.2 ainda não possui proteção real de API. Isso deve ser corrigido na versão 0.2.0.
