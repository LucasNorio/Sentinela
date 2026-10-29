# Guia de publicação — Sentinela v0.5.0

Este diretório é uma **cópia publicável** do projeto funcional. A pasta original com `.env`, `.venv` e seu banco MySQL deve permanecer intacta.

## Revisão antes do commit

1. Leia o `README.md`, `CHANGELOG.md` e `RELEASE_NOTES_v0.5.0.md`.
2. Configure `.env` localmente a partir de `.env.example` e teste em uma cópia do projeto. A distribuição não contém `.env` nem `.venv`.
3. Atenção: o `app.py` agora inicia em `127.0.0.1` e sem debug. Para testes com ESP32 na rede local, configure `FLASK_HOST=0.0.0.0` e mantenha `FLASK_DEBUG=0`.
4. O script de usuários iniciais exige senha configurada em `SENTINELA_ADMIN_PASSWORD` (12 ou mais caracteres). **Não redefine** usuários existentes.
5. Instale as dependências e confirme os testes:

   ```powershell
   python -m pip install -r requirements.txt
   python -m unittest discover -s tests -v
   ```

6. Revise os dados que deseja compartilhar; relatórios contendo nomes reais, exportações do MySQL e segredos não devem ser incluídos.

## Atualização segura do GitHub

Execute os comandos **na pasta do seu clone Git**, não no diretório do ZIP:

```powershell
# Já na pasta do clone do GitHub:
git status --short
git branch --show-current
git pull --ff-only origin main
```

Copie os arquivos da pasta publicável para o clone, substituindo os correspondentes. Não copie `.git`, `.env` nem `.venv`. Depois:

```powershell
git status --short
git add -A
git diff --cached --check
git diff --cached --stat
git ls-files --cached -- .env
git commit -m "feat: adicionar relatorios academicos em PDF v0.5.0"
git push origin main
```

O resultado de `git ls-files --cached -- .env` deve ser vazio. Confira o hash do commit **após o push**:

```powershell
git rev-parse HEAD
git rev-parse origin/main
```

Os dois valores devem ser iguais. **Somente então**, se `v0.5.0` ainda não existir:

```powershell
git tag -a v0.5.0 -m "Sentinela v0.5.0 - Relatorios Academicos"
git push origin v0.5.0
```

Verifique que a tag aponta para o commit publicado:

```powershell
git rev-list -n 1 v0.5.0
git rev-parse origin/main
```

Abra `https://github.com/LucasNorio/Sentinela/releases/new`, selecione `v0.5.0`, utilize o título **Sentinela v0.5.0 — Relatórios Acadêmicos** e aproveite o conteúdo de `RELEASE_NOTES_v0.5.0.md` como descrição.

> Não utilize `git push --force` para publicar a nova versão. Se `v0.5.0` já existir, verifique seu destino antes de criar ou mover tags.

## Conferência pós-publicação

- Baixe `Source code (zip)` da release e confirme `routes/relatorios_routes.py`, `.env.example`, `RELEASE_NOTES_v0.5.0.md` e os dois testes em `tests/`.
- Confira que não há `.env`, `.venv`, backups pessoais ou pacotes ZIP aninhados no arquivo disponibilizado.
- Compare o commit de `v0.5.0` com o commit da branch `main`.
- O GitHub **não** é atualizado automaticamente por gerar esta cópia publicável; a publicação exige sua ação no repositório.
