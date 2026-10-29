"""Provisionamento explícito de contas de desenvolvimento do Sentinela.

Configure SENTINELA_*_PASSWORD no .env antes de executar este script.
Por segurança, ele nunca sobrescreve credenciais de contas existentes.
"""

import os
from pathlib import Path
import sys

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))

from werkzeug.security import generate_password_hash
from database import obter_conexao

CONTAS_INICIAIS = (
    ('Administrador', 'admin@sentinela.com', 'Administrador', 'SENTINELA_ADMIN_PASSWORD'),
    ('Coordenação', 'coordenacao@sentinela.com', 'Coordenação', 'SENTINELA_COORDENACAO_PASSWORD'),
    ('Secretaria', 'secretaria@sentinela.com', 'Secretaria', 'SENTINELA_SECRETARIA_PASSWORD'),
    ('Professor', 'professor@sentinela.com', 'Professor', 'SENTINELA_PROFESSOR_PASSWORD'),
)


def main():
    contas = []
    for nome, email, perfil, variavel in CONTAS_INICIAIS:
        senha = os.getenv(variavel, '')
        if not senha:
            continue
        if len(senha) < 12:
            raise SystemExit(
                f'A variável {variavel} precisa conter uma senha com pelo menos 12 caracteres.'
            )
        contas.append((nome, email, perfil, senha))

    if not contas:
        raise SystemExit(
            'Configure SENTINELA_ADMIN_PASSWORD no arquivo .env antes de executar o script.'
        )

    conexao = obter_conexao()
    if conexao is None:
        raise SystemExit('Não foi possível conectar ao banco de dados.')

    cursor = None
    try:
        cursor = conexao.cursor(dictionary=True)
        for nome, email, perfil, senha in contas:
            cursor.execute(
                'SELECT id_usuario FROM usuario WHERE email = %s',
                (email,),
            )
            if cursor.fetchone():
                print(f'Conta existente preservada: {email}')
                continue

            cursor.execute(
                '''
                INSERT INTO usuario (nome, email, senha_hash, perfil, status)
                VALUES (%s, %s, %s, %s, 'Ativo')
                ''',
                (nome, email, generate_password_hash(senha), perfil),
            )
            print(f'Conta inicial criada: {email} ({perfil})')

        conexao.commit()
        print('Provisionamento finalizado. As senhas não são exibidas.')
    except Exception:
        conexao.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


if __name__ == '__main__':
    main()
