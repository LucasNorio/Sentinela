# Modelo de dados

A versão 0.1.2 usa MySQL e contém as entidades principais do domínio escolar e RFID.

## Entidades principais

```txt
curso
turma
aluno
tag_rfid
professor
professor_turma
ambiente
leitor_rfid
registro_rfid
```

## Relações principais

```txt
curso 1:N turma
turma 1:N aluno
aluno 1:N tag_rfid
professor N:N turma, por professor_turma
ambiente 1:N leitor_rfid
leitor_rfid 1:N registro_rfid
ambiente 1:N registro_rfid
aluno 1:N registro_rfid
tag_rfid 1:N registro_rfid
```

## Preservação histórica

O sistema segue a regra de evitar exclusão física de dados importantes.

Em vez de apagar registros, usa status como:

```txt
Ativo
Inativo
Manutenção
Encerrada
Bloqueada
Perdida
```

Isso preserva o histórico de vínculos, registros e movimentações.

## Scripts

A estrutura inicial está em:

```txt
database/schema.sql
```

Dados iniciais mínimos estão em:

```txt
database/seed.sql
```
