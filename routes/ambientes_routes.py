from flask import Blueprint, jsonify, request
from mysql.connector import Error
from database import obter_conexao

ambientes_bp = Blueprint('ambientes', __name__)

TIPOS_AMBIENTE_VALIDOS = {
    'Portaria',
    'Sala',
    'Laboratório',
    'Biblioteca',
    'Oficina',
    'Pátio',
    'Secretaria',
    'Coordenação',
    'Área comum',
    'Outro'
}

STATUS_AMBIENTE_VALIDOS = {
    'Ativo',
    'Inativo',
    'Manutenção'
}


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def validar_ambiente(dados):
    nome = str(dados.get('nome', '')).strip()
    bloco = str(dados.get('bloco', '')).strip()
    tipo = dados.get('tipo')
    capacidade = dados.get('capacidade')
    status = dados.get('status', 'Ativo')

    if not nome:
        return None, 'O nome do ambiente é obrigatório.'

    if not bloco:
        return None, 'O bloco/localização do ambiente é obrigatório.'

    if not tipo:
        return None, 'O tipo do ambiente é obrigatório.'

    if tipo not in TIPOS_AMBIENTE_VALIDOS:
        return None, 'Tipo de ambiente inválido.'

    if status not in STATUS_AMBIENTE_VALIDOS:
        return None, 'Status de ambiente inválido.'

    if capacidade == '':
        capacidade = None

    if capacidade is not None:
        try:
            capacidade = int(capacidade)
        except (ValueError, TypeError):
            return None, 'A capacidade deve ser um número inteiro.'

        if capacidade <= 0:
            return None, 'A capacidade deve ser maior que zero.'

    return {
        'nome': nome,
        'bloco': bloco,
        'tipo': tipo,
        'capacidade': capacidade,
        'status': status
    }, None


@ambientes_bp.get('/api/ambientes')
def listar_ambientes():
    status = request.args.get('status', 'Todos')

    if status != 'Todos' and status not in STATUS_AMBIENTE_VALIDOS:
        return resposta_erro('Status inválido.')

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        if status == 'Todos':
            cursor.execute("""
                SELECT
                    id_ambiente AS id,
                    nome,
                    bloco,
                    tipo,
                    capacidade,
                    status,
                    CAST(criado_em AS CHAR) AS criado_em,
                    CAST(inativado_em AS CHAR) AS inativado_em,
                    motivo_inativacao,
                    CAST(manutencao_em AS CHAR) AS manutencao_em,
                    motivo_manutencao
                FROM ambiente
                ORDER BY nome
            """)
        else:
            cursor.execute("""
                SELECT
                    id_ambiente AS id,
                    nome,
                    bloco,
                    tipo,
                    capacidade,
                    status,
                    CAST(criado_em AS CHAR) AS criado_em,
                    CAST(inativado_em AS CHAR) AS inativado_em,
                    motivo_inativacao,
                    CAST(manutencao_em AS CHAR) AS manutencao_em,
                    motivo_manutencao
                FROM ambiente
                WHERE status = %s
                ORDER BY nome
            """, (status,))

        return jsonify(cursor.fetchall())

    except Error as erro:
        return resposta_erro(f'Erro ao listar ambientes: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@ambientes_bp.post('/api/ambientes')
def cadastrar_ambiente():
    dados = request.get_json(silent=True) or {}
    ambiente, erro_validacao = validar_ambiente(dados)

    if erro_validacao:
        return resposta_erro(erro_validacao)

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor()
        conexao.start_transaction()

        if ambiente['status'] == 'Inativo':
            cursor.execute("""
                INSERT INTO ambiente
                    (
                        nome,
                        bloco,
                        tipo,
                        capacidade,
                        status,
                        inativado_em,
                        motivo_inativacao
                    )
                VALUES
                    (%s, %s, %s, %s, %s, NOW(), %s)
            """, (
                ambiente['nome'],
                ambiente['bloco'],
                ambiente['tipo'],
                ambiente['capacidade'],
                ambiente['status'],
                'Ambiente cadastrado como inativo.'
            ))

        elif ambiente['status'] == 'Manutenção':
            cursor.execute("""
                INSERT INTO ambiente
                    (
                        nome,
                        bloco,
                        tipo,
                        capacidade,
                        status,
                        manutencao_em,
                        motivo_manutencao
                    )
                VALUES
                    (%s, %s, %s, %s, %s, NOW(), %s)
            """, (
                ambiente['nome'],
                ambiente['bloco'],
                ambiente['tipo'],
                ambiente['capacidade'],
                ambiente['status'],
                'Ambiente cadastrado em manutenção.'
            ))

        else:
            cursor.execute("""
                INSERT INTO ambiente
                    (nome, bloco, tipo, capacidade, status)
                VALUES
                    (%s, %s, %s, %s, %s)
            """, (
                ambiente['nome'],
                ambiente['bloco'],
                ambiente['tipo'],
                ambiente['capacidade'],
                ambiente['status']
            ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Ambiente cadastrado com sucesso.',
            'id_ambiente': cursor.lastrowid
        }), 201

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar ambiente: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@ambientes_bp.put('/api/ambientes/<int:id_ambiente>')
def atualizar_ambiente(id_ambiente):
    dados = request.get_json(silent=True) or {}
    ambiente, erro_validacao = validar_ambiente(dados)

    if erro_validacao:
        return resposta_erro(erro_validacao)

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_ambiente
            FROM ambiente
            WHERE id_ambiente = %s
        """, (id_ambiente,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Ambiente não encontrado.', 404)

        if ambiente['status'] == 'Ativo':
            cursor.execute("""
                UPDATE ambiente
                SET
                    nome = %s,
                    bloco = %s,
                    tipo = %s,
                    capacidade = %s,
                    status = 'Ativo',
                    inativado_em = NULL,
                    motivo_inativacao = NULL,
                    manutencao_em = NULL,
                    motivo_manutencao = NULL
                WHERE id_ambiente = %s
            """, (
                ambiente['nome'],
                ambiente['bloco'],
                ambiente['tipo'],
                ambiente['capacidade'],
                id_ambiente
            ))

        elif ambiente['status'] == 'Inativo':
            cursor.execute("""
                UPDATE ambiente
                SET
                    nome = %s,
                    bloco = %s,
                    tipo = %s,
                    capacidade = %s,
                    status = 'Inativo',
                    inativado_em = COALESCE(inativado_em, NOW()),
                    motivo_inativacao = COALESCE(motivo_inativacao, 'Ambiente atualizado como inativo.'),
                    manutencao_em = NULL,
                    motivo_manutencao = NULL
                WHERE id_ambiente = %s
            """, (
                ambiente['nome'],
                ambiente['bloco'],
                ambiente['tipo'],
                ambiente['capacidade'],
                id_ambiente
            ))

        else:
            cursor.execute("""
                UPDATE ambiente
                SET
                    nome = %s,
                    bloco = %s,
                    tipo = %s,
                    capacidade = %s,
                    status = 'Manutenção',
                    inativado_em = NULL,
                    motivo_inativacao = NULL,
                    manutencao_em = COALESCE(manutencao_em, NOW()),
                    motivo_manutencao = COALESCE(motivo_manutencao, 'Ambiente atualizado para manutenção.')
                WHERE id_ambiente = %s
            """, (
                ambiente['nome'],
                ambiente['bloco'],
                ambiente['tipo'],
                ambiente['capacidade'],
                id_ambiente
            ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Ambiente atualizado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar ambiente: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@ambientes_bp.patch('/api/ambientes/<int:id_ambiente>/inativar')
def inativar_ambiente(id_ambiente):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Ambiente inativado pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Ambiente inativado pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_ambiente, status
            FROM ambiente
            WHERE id_ambiente = %s
        """, (id_ambiente,))

        ambiente = cursor.fetchone()

        if ambiente is None:
            conexao.rollback()
            return resposta_erro('Ambiente não encontrado.', 404)

        if ambiente['status'] == 'Inativo':
            conexao.rollback()
            return resposta_erro('Ambiente já está inativo.', 409)

        cursor.execute("""
            UPDATE ambiente
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s,
                manutencao_em = NULL,
                motivo_manutencao = NULL
            WHERE id_ambiente = %s
        """, (
            motivo,
            id_ambiente
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Ambiente inativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar ambiente: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@ambientes_bp.patch('/api/ambientes/<int:id_ambiente>/reativar')
def reativar_ambiente(id_ambiente):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_ambiente, status
            FROM ambiente
            WHERE id_ambiente = %s
        """, (id_ambiente,))

        ambiente = cursor.fetchone()

        if ambiente is None:
            conexao.rollback()
            return resposta_erro('Ambiente não encontrado.', 404)

        if ambiente['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Ambiente já está ativo.', 409)

        cursor.execute("""
            UPDATE ambiente
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL,
                manutencao_em = NULL,
                motivo_manutencao = NULL
            WHERE id_ambiente = %s
        """, (id_ambiente,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Ambiente reativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar ambiente: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@ambientes_bp.patch('/api/ambientes/<int:id_ambiente>/manutencao')
def colocar_ambiente_em_manutencao(id_ambiente):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Ambiente colocado em manutenção.')).strip()

    if motivo == '':
        motivo = 'Ambiente colocado em manutenção.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_ambiente, status
            FROM ambiente
            WHERE id_ambiente = %s
        """, (id_ambiente,))

        ambiente = cursor.fetchone()

        if ambiente is None:
            conexao.rollback()
            return resposta_erro('Ambiente não encontrado.', 404)

        if ambiente['status'] == 'Manutenção':
            conexao.rollback()
            return resposta_erro('Ambiente já está em manutenção.', 409)

        cursor.execute("""
            UPDATE ambiente
            SET
                status = 'Manutenção',
                inativado_em = NULL,
                motivo_inativacao = NULL,
                manutencao_em = NOW(),
                motivo_manutencao = %s
            WHERE id_ambiente = %s
        """, (
            motivo,
            id_ambiente
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Ambiente colocado em manutenção com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao colocar ambiente em manutenção: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()