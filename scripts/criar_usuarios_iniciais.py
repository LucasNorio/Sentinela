from pathlib import Path
import sys

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.append(str(RAIZ_PROJETO))

from werkzeug.security import generate_password_hash
from database import obter_conexao

usuarios = [
    {
        'nome': 'Administrador',
        'email': 'admin@sentinela.com',
        'senha': 'admin123',
        'perfil': 'Administrador'
    },
    {
        'nome': 'Coordenação Teste',
        'email': 'coordenacao@sentinela.com',
        'senha': 'coord123',
        'perfil': 'Coordenação'
    },
    {
        'nome': 'Secretaria Teste',
        'email': 'secretaria@sentinela.com',
        'senha': 'sec123',
        'perfil': 'Secretaria'
    },
    {
        'nome': 'Professor Teste',
        'email': 'professor@sentinela.com',
        'senha': 'prof123',
        'perfil': 'Professor'
    }
]

conexao = obter_conexao()

if conexao is None:
    print('Erro ao conectar ao banco de dados.')
    raise SystemExit

cursor = None

try:
    cursor = conexao.cursor(dictionary=True)

    for usuario in usuarios:
        senha_hash = generate_password_hash(usuario['senha'])

        cursor.execute("""
            SELECT id_usuario
            FROM usuario
            WHERE email = %s
        """, (usuario['email'],))

        existente = cursor.fetchone()

        if existente:
            cursor.execute("""
                UPDATE usuario
                SET
                    nome = %s,
                    senha_hash = %s,
                    perfil = %s,
                    status = 'Ativo',
                    inativado_em = NULL,
                    motivo_inativacao = NULL,
                    atualizado_em = NOW()
                WHERE id_usuario = %s
            """, (
                usuario['nome'],
                senha_hash,
                usuario['perfil'],
                existente['id_usuario']
            ))
        else:
            cursor.execute("""
                INSERT INTO usuario
                    (nome, email, senha_hash, perfil, status)
                VALUES
                    (%s, %s, %s, %s, 'Ativo')
            """, (
                usuario['nome'],
                usuario['email'],
                senha_hash,
                usuario['perfil']
            ))

    conexao.commit()

    print('Usuários iniciais criados/atualizados com sucesso.')
    print()
    print('Credenciais de desenvolvimento:')
    print('Administrador: admin@sentinela.com / admin123')
    print('Coordenação: coordenacao@sentinela.com / coord123')
    print('Secretaria: secretaria@sentinela.com / sec123')
    print('Professor: professor@sentinela.com / prof123')

finally:
    if cursor:
        cursor.close()

    conexao.close()