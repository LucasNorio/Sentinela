from functools import wraps
from flask import Blueprint, jsonify, request, session, redirect
from werkzeug.security import check_password_hash
from mysql.connector import Error
from database import obter_conexao

auth_bp = Blueprint('auth', __name__)

PERFIS_VALIDOS = {
    'Administrador',
    'Coordenação',
    'Secretaria',
    'Professor'
}


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def usuario_logado():
    return session.get('usuario')


def login_obrigatorio(funcao):
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        if not usuario_logado():
            if request.path.startswith('/api/'):
                return resposta_erro('Usuário não autenticado.', 401)

            return redirect('/')

        return funcao(*args, **kwargs)

    return wrapper


def perfil_obrigatorio(*perfis_permitidos):
    def decorador(funcao):
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            usuario = usuario_logado()

            if not usuario:
                if request.path.startswith('/api/'):
                    return resposta_erro('Usuário não autenticado.', 401)

                return redirect('/')

            if usuario.get('perfil') not in perfis_permitidos:
                return resposta_erro('Usuário sem permissão para esta ação.', 403)

            return funcao(*args, **kwargs)

        return wrapper

    return decorador


def montar_usuario_sessao(usuario):
    return {
        'id': usuario['id'],
        'nome': usuario['nome'],
        'email': usuario['email'],
        'perfil': usuario['perfil']
    }


@auth_bp.post('/api/auth/login')
def login():
    dados = request.get_json(silent=True) or {}

    email = str(dados.get('email', '')).strip().lower()
    senha = str(dados.get('senha', '')).strip()

    if not email:
        return resposta_erro('O e-mail é obrigatório.')

    if not senha:
        return resposta_erro('A senha é obrigatória.')

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id_usuario AS id,
                nome,
                email,
                senha_hash,
                perfil,
                status
            FROM usuario
            WHERE email = %s
        """, (email,))

        usuario = cursor.fetchone()

        if usuario is None:
            return resposta_erro('E-mail ou senha inválidos.', 401)

        if usuario['status'] != 'Ativo':
            return resposta_erro('Usuário inativo. Contate o administrador.', 403)

        if usuario['perfil'] not in PERFIS_VALIDOS:
            return resposta_erro('Perfil de usuário inválido.', 403)

        if not check_password_hash(usuario['senha_hash'], senha):
            return resposta_erro('E-mail ou senha inválidos.', 401)

        cursor.execute("""
            UPDATE usuario
            SET ultimo_login = NOW()
            WHERE id_usuario = %s
        """, (usuario['id'],))

        conexao.commit()

        session.clear()
        session['usuario'] = montar_usuario_sessao(usuario)

        return jsonify({
            'mensagem': 'Login realizado com sucesso.',
            'usuario': session['usuario']
        })

    except Error as erro:
        return resposta_erro(f'Erro ao realizar login: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@auth_bp.post('/api/auth/logout')
def logout():
    session.clear()

    return jsonify({
        'mensagem': 'Logout realizado com sucesso.'
    })


@auth_bp.get('/api/auth/me')
def obter_usuario_autenticado():
    usuario = usuario_logado()

    if not usuario:
        return resposta_erro('Usuário não autenticado.', 401)

    return jsonify({
        'usuario': usuario
    })