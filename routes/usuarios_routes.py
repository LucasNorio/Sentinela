from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from mysql.connector import Error, IntegrityError
from database import obter_conexao
from routes.auth_routes import perfil_obrigatorio, usuario_logado

usuarios_bp = Blueprint('usuarios', __name__)

PERFIS_VALIDOS = {
    'Administrador',
    'Coordenação',
    'Secretaria',
    'Professor'
}

STATUS_VALIDOS = {
    'Ativo',
    'Inativo'
}


@usuarios_bp.before_request
@perfil_obrigatorio('Administrador')
def proteger_rotas_usuarios():
    pass


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def validar_usuario(dados, criacao=True):
    nome = str(dados.get('nome', '')).strip()
    email = str(dados.get('email', '')).strip().lower()
    perfil = str(dados.get('perfil', '')).strip()

    senha = str(dados.get('senha', '')).strip()

    if not nome:
        return None, 'O nome é obrigatório.'

    if not email:
        return None, 'O e-mail é obrigatório.'

    if '@' not in email:
        return None, 'Informe um e-mail válido.'

    if perfil not in PERFIS_VALIDOS:
        return None, 'Perfil de usuário inválido.'

    if criacao:
        if not senha:
            return None, 'A senha é obrigatória.'

        if len(senha) < 6:
            return None, 'A senha deve ter pelo menos 6 caracteres.'

    return {
        'nome': nome,
        'email': email,
        'perfil': perfil,
        'senha': senha
    }, None


def buscar_usuario_por_id(cursor, id_usuario):
    cursor.execute("""
        SELECT
            id_usuario,
            nome,
            email,
            perfil,
            status
        FROM usuario
        WHERE id_usuario = %s
    """, (id_usuario,))

    return cursor.fetchone()


@usuarios_bp.get('/api/usuarios')
def listar_usuarios():
    status_filtro = request.args.get('status', 'Todos')
    perfil_filtro = request.args.get('perfil', 'Todos')
    busca = request.args.get('busca', '').strip()

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                id_usuario AS id,
                nome,
                email,
                perfil,
                status,
                CAST(criado_em AS CHAR) AS criado_em,
                CAST(atualizado_em AS CHAR) AS atualizado_em,
                CAST(ultimo_login AS CHAR) AS ultimo_login,
                CAST(inativado_em AS CHAR) AS inativado_em,
                motivo_inativacao
            FROM usuario
            WHERE 1 = 1
        """

        parametros = []

        if status_filtro in STATUS_VALIDOS:
            sql += " AND status = %s"
            parametros.append(status_filtro)

        if perfil_filtro in PERFIS_VALIDOS:
            sql += " AND perfil = %s"
            parametros.append(perfil_filtro)

        if busca:
            sql += """
                AND (
                    nome LIKE %s
                    OR email LIKE %s
                    OR perfil LIKE %s
                )
            """
            termo = f'%{busca}%'
            parametros.extend([termo, termo, termo])

        sql += """
            ORDER BY
                status ASC,
                nome ASC
        """

        cursor.execute(sql, parametros)
        usuarios = cursor.fetchall()

        return jsonify(usuarios)

    except Error as erro:
        return resposta_erro(f'Erro ao listar usuários: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@usuarios_bp.post('/api/usuarios')
def criar_usuario():
    dados = request.get_json(silent=True) or {}

    usuario_validado, erro = validar_usuario(dados, criacao=True)

    if erro:
        return resposta_erro(erro)

    senha_hash = generate_password_hash(usuario_validado['senha'])

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO usuario
                (nome, email, senha_hash, perfil, status)
            VALUES
                (%s, %s, %s, %s, 'Ativo')
        """, (
            usuario_validado['nome'],
            usuario_validado['email'],
            senha_hash,
            usuario_validado['perfil']
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Usuário criado com sucesso.',
            'id': cursor.lastrowid
        }), 201

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Já existe um usuário cadastrado com este e-mail.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao criar usuário: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@usuarios_bp.put('/api/usuarios/<int:id_usuario>')
def atualizar_usuario(id_usuario):
    dados = request.get_json(silent=True) or {}

    usuario_validado, erro = validar_usuario(dados, criacao=False)

    if erro:
        return resposta_erro(erro)

    usuario_atual = usuario_logado()

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        usuario_existente = buscar_usuario_por_id(cursor, id_usuario)

        if usuario_existente is None:
            return resposta_erro('Usuário não encontrado.', 404)

        if usuario_atual and usuario_atual.get('id') == id_usuario:
            if usuario_validado['perfil'] != 'Administrador':
                return resposta_erro('Você não pode remover seu próprio perfil de administrador.', 403)

        cursor.execute("""
            UPDATE usuario
            SET
                nome = %s,
                email = %s,
                perfil = %s,
                atualizado_em = NOW()
            WHERE id_usuario = %s
        """, (
            usuario_validado['nome'],
            usuario_validado['email'],
            usuario_validado['perfil'],
            id_usuario
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Usuário atualizado com sucesso.'
        })

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Já existe um usuário cadastrado com este e-mail.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar usuário: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@usuarios_bp.patch('/api/usuarios/<int:id_usuario>/inativar')
def inativar_usuario(id_usuario):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', '')).strip()

    if not motivo:
        motivo = 'Inativação realizada pelo administrador.'

    usuario_atual = usuario_logado()

    if usuario_atual and usuario_atual.get('id') == id_usuario:
        return resposta_erro('Você não pode inativar o próprio usuário logado.', 403)

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        usuario_existente = buscar_usuario_por_id(cursor, id_usuario)

        if usuario_existente is None:
            return resposta_erro('Usuário não encontrado.', 404)

        if usuario_existente['status'] == 'Inativo':
            return resposta_erro('Usuário já está inativo.', 409)

        cursor.execute("""
            UPDATE usuario
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s,
                atualizado_em = NOW()
            WHERE id_usuario = %s
        """, (
            motivo,
            id_usuario
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Usuário inativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar usuário: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@usuarios_bp.patch('/api/usuarios/<int:id_usuario>/reativar')
def reativar_usuario(id_usuario):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        usuario_existente = buscar_usuario_por_id(cursor, id_usuario)

        if usuario_existente is None:
            return resposta_erro('Usuário não encontrado.', 404)

        if usuario_existente['status'] == 'Ativo':
            return resposta_erro('Usuário já está ativo.', 409)

        cursor.execute("""
            UPDATE usuario
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL,
                atualizado_em = NOW()
            WHERE id_usuario = %s
        """, (id_usuario,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Usuário reativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar usuário: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@usuarios_bp.patch('/api/usuarios/<int:id_usuario>/resetar-senha')
def resetar_senha_usuario(id_usuario):
    dados = request.get_json(silent=True) or {}
    nova_senha = str(dados.get('nova_senha', '')).strip()

    if not nova_senha:
        return resposta_erro('A nova senha é obrigatória.')

    if len(nova_senha) < 6:
        return resposta_erro('A nova senha deve ter pelo menos 6 caracteres.')

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        usuario_existente = buscar_usuario_por_id(cursor, id_usuario)

        if usuario_existente is None:
            return resposta_erro('Usuário não encontrado.', 404)

        senha_hash = generate_password_hash(nova_senha)

        cursor.execute("""
            UPDATE usuario
            SET
                senha_hash = %s,
                atualizado_em = NOW()
            WHERE id_usuario = %s
        """, (
            senha_hash,
            id_usuario
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Senha redefinida com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao redefinir senha: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()