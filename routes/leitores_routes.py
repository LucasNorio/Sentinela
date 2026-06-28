import re
from flask import Blueprint, jsonify, request
from mysql.connector import Error, IntegrityError
from database import obter_conexao

leitores_bp = Blueprint('leitores', __name__)

TIPOS_LEITOR_VALIDOS = {
    'Entrada',
    'Saída',
    'Entrada/Saída',
    'Interno',
    'Outro'
}

STATUS_LEITOR_VALIDOS = {
    'Ativo',
    'Inativo',
    'Manutenção'
}


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def validar_leitor(dados):
    id_ambiente = dados.get('id_ambiente')
    nome = str(dados.get('nome', '')).strip()
    codigo_identificacao = str(dados.get('codigo_identificacao', '')).strip().upper()
    tipo_leitor = dados.get('tipo_leitor', 'Interno')
    status = dados.get('status', 'Ativo')

    if not id_ambiente:
        return None, 'O ambiente é obrigatório.'

    try:
        id_ambiente = int(id_ambiente)
    except (ValueError, TypeError):
        return None, 'Ambiente inválido.'

    if not nome:
        return None, 'O nome do leitor é obrigatório.'

    if not codigo_identificacao:
        return None, 'O código de identificação é obrigatório.'

    if not re.fullmatch(r'[A-Z0-9_-]+', codigo_identificacao):
        return None, 'O código deve conter apenas letras, números, _ ou -.'

    if tipo_leitor not in TIPOS_LEITOR_VALIDOS:
        return None, 'Tipo de leitor inválido.'

    if status not in STATUS_LEITOR_VALIDOS:
        return None, 'Status de leitor inválido.'

    return {
        'id_ambiente': id_ambiente,
        'nome': nome,
        'codigo_identificacao': codigo_identificacao,
        'tipo_leitor': tipo_leitor,
        'status': status
    }, None


@leitores_bp.get('/api/leitores-rfid')
def listar_leitores():
    status = request.args.get('status', 'Todos')

    if status != 'Todos' and status not in STATUS_LEITOR_VALIDOS:
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
                    l.id_leitor AS id,
                    l.id_ambiente,
                    l.codigo_identificacao,
                    l.tipo_leitor,
                    l.nome,
                    l.status,
                    CAST(l.instalado_em AS CHAR) AS instalado_em,
                    CAST(l.ultima_comunicacao AS CHAR) AS ultima_comunicacao,
                    CAST(l.inativado_em AS CHAR) AS inativado_em,
                    l.motivo_inativacao,
                    CAST(l.manutencao_em AS CHAR) AS manutencao_em,
                    l.motivo_manutencao,
                    a.nome AS ambiente,
                    a.bloco,
                    a.tipo AS tipo_ambiente,
                    a.status AS status_ambiente
                FROM leitor_rfid l
                INNER JOIN ambiente a ON a.id_ambiente = l.id_ambiente
                ORDER BY l.nome
            """)
        else:
            cursor.execute("""
                SELECT
                    l.id_leitor AS id,
                    l.id_ambiente,
                    l.codigo_identificacao,
                    l.tipo_leitor,
                    l.nome,
                    l.status,
                    CAST(l.instalado_em AS CHAR) AS instalado_em,
                    CAST(l.ultima_comunicacao AS CHAR) AS ultima_comunicacao,
                    CAST(l.inativado_em AS CHAR) AS inativado_em,
                    l.motivo_inativacao,
                    CAST(l.manutencao_em AS CHAR) AS manutencao_em,
                    l.motivo_manutencao,
                    a.nome AS ambiente,
                    a.bloco,
                    a.tipo AS tipo_ambiente,
                    a.status AS status_ambiente
                FROM leitor_rfid l
                INNER JOIN ambiente a ON a.id_ambiente = l.id_ambiente
                WHERE l.status = %s
                ORDER BY l.nome
            """, (status,))

        return jsonify(cursor.fetchall())

    except Error as erro:
        return resposta_erro(f'Erro ao listar leitores RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@leitores_bp.post('/api/leitores-rfid')
def cadastrar_leitor():
    dados = request.get_json(silent=True) or {}
    leitor, erro_validacao = validar_leitor(dados)

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
            SELECT id_ambiente, status
            FROM ambiente
            WHERE id_ambiente = %s
        """, (leitor['id_ambiente'],))

        ambiente = cursor.fetchone()

        if ambiente is None:
            conexao.rollback()
            return resposta_erro('Ambiente não encontrado.', 404)

        if ambiente['status'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível cadastrar leitor em ambiente inativo ou em manutenção.', 409)

        if leitor['status'] == 'Inativo':
            cursor.execute("""
                INSERT INTO leitor_rfid
                    (
                        id_ambiente,
                        nome,
                        codigo_identificacao,
                        tipo_leitor,
                        status,
                        inativado_em,
                        motivo_inativacao
                    )
                VALUES
                    (%s, %s, %s, %s, %s, NOW(), %s)
            """, (
                leitor['id_ambiente'],
                leitor['nome'],
                leitor['codigo_identificacao'],
                leitor['tipo_leitor'],
                leitor['status'],
                'Leitor cadastrado como inativo.'
            ))

        elif leitor['status'] == 'Manutenção':
            cursor.execute("""
                INSERT INTO leitor_rfid
                    (
                        id_ambiente,
                        nome,
                        codigo_identificacao,
                        tipo_leitor,
                        status,
                        manutencao_em,
                        motivo_manutencao
                    )
                VALUES
                    (%s, %s, %s, %s, %s, NOW(), %s)
            """, (
                leitor['id_ambiente'],
                leitor['nome'],
                leitor['codigo_identificacao'],
                leitor['tipo_leitor'],
                leitor['status'],
                'Leitor cadastrado em manutenção.'
            ))

        else:
            cursor.execute("""
                INSERT INTO leitor_rfid
                    (
                        id_ambiente,
                        nome,
                        codigo_identificacao,
                        tipo_leitor,
                        status
                    )
                VALUES
                    (%s, %s, %s, %s, %s)
            """, (
                leitor['id_ambiente'],
                leitor['nome'],
                leitor['codigo_identificacao'],
                leitor['tipo_leitor'],
                leitor['status']
            ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Leitor RFID cadastrado com sucesso.',
            'id_leitor': cursor.lastrowid
        }), 201

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Já existe um leitor com este código de identificação.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar leitor RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@leitores_bp.put('/api/leitores-rfid/<int:id_leitor>')
def atualizar_leitor(id_leitor):
    dados = request.get_json(silent=True) or {}
    leitor, erro_validacao = validar_leitor(dados)

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
            SELECT id_leitor
            FROM leitor_rfid
            WHERE id_leitor = %s
        """, (id_leitor,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Leitor RFID não encontrado.', 404)

        cursor.execute("""
            SELECT id_ambiente, status
            FROM ambiente
            WHERE id_ambiente = %s
        """, (leitor['id_ambiente'],))

        ambiente = cursor.fetchone()

        if ambiente is None:
            conexao.rollback()
            return resposta_erro('Ambiente não encontrado.', 404)

        if ambiente['status'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível vincular leitor a ambiente inativo ou em manutenção.', 409)

        if leitor['status'] == 'Ativo':
            cursor.execute("""
                UPDATE leitor_rfid
                SET
                    id_ambiente = %s,
                    nome = %s,
                    codigo_identificacao = %s,
                    tipo_leitor = %s,
                    status = 'Ativo',
                    inativado_em = NULL,
                    motivo_inativacao = NULL,
                    manutencao_em = NULL,
                    motivo_manutencao = NULL
                WHERE id_leitor = %s
            """, (
                leitor['id_ambiente'],
                leitor['nome'],
                leitor['codigo_identificacao'],
                leitor['tipo_leitor'],
                id_leitor
            ))

        elif leitor['status'] == 'Inativo':
            cursor.execute("""
                UPDATE leitor_rfid
                SET
                    id_ambiente = %s,
                    nome = %s,
                    codigo_identificacao = %s,
                    tipo_leitor = %s,
                    status = 'Inativo',
                    inativado_em = COALESCE(inativado_em, NOW()),
                    motivo_inativacao = COALESCE(motivo_inativacao, 'Leitor atualizado como inativo.'),
                    manutencao_em = NULL,
                    motivo_manutencao = NULL
                WHERE id_leitor = %s
            """, (
                leitor['id_ambiente'],
                leitor['nome'],
                leitor['codigo_identificacao'],
                leitor['tipo_leitor'],
                id_leitor
            ))

        else:
            cursor.execute("""
                UPDATE leitor_rfid
                SET
                    id_ambiente = %s,
                    nome = %s,
                    codigo_identificacao = %s,
                    tipo_leitor = %s,
                    status = 'Manutenção',
                    inativado_em = NULL,
                    motivo_inativacao = NULL,
                    manutencao_em = COALESCE(manutencao_em, NOW()),
                    motivo_manutencao = COALESCE(motivo_manutencao, 'Leitor atualizado para manutenção.')
                WHERE id_leitor = %s
            """, (
                leitor['id_ambiente'],
                leitor['nome'],
                leitor['codigo_identificacao'],
                leitor['tipo_leitor'],
                id_leitor
            ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Leitor RFID atualizado com sucesso.'
        })

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Já existe um leitor com este código de identificação.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar leitor RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@leitores_bp.patch('/api/leitores-rfid/<int:id_leitor>/inativar')
def inativar_leitor(id_leitor):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Leitor RFID inativado pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Leitor RFID inativado pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_leitor, status
            FROM leitor_rfid
            WHERE id_leitor = %s
        """, (id_leitor,))

        leitor = cursor.fetchone()

        if leitor is None:
            conexao.rollback()
            return resposta_erro('Leitor RFID não encontrado.', 404)

        if leitor['status'] == 'Inativo':
            conexao.rollback()
            return resposta_erro('Leitor RFID já está inativo.', 409)

        cursor.execute("""
            UPDATE leitor_rfid
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s,
                manutencao_em = NULL,
                motivo_manutencao = NULL
            WHERE id_leitor = %s
        """, (
            motivo,
            id_leitor
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Leitor RFID inativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar leitor RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@leitores_bp.patch('/api/leitores-rfid/<int:id_leitor>/reativar')
def reativar_leitor(id_leitor):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT
                l.id_leitor,
                l.status,
                a.status AS status_ambiente
            FROM leitor_rfid l
            INNER JOIN ambiente a ON a.id_ambiente = l.id_ambiente
            WHERE l.id_leitor = %s
        """, (id_leitor,))

        leitor = cursor.fetchone()

        if leitor is None:
            conexao.rollback()
            return resposta_erro('Leitor RFID não encontrado.', 404)

        if leitor['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Leitor RFID já está ativo.', 409)

        if leitor['status_ambiente'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível reativar leitor de ambiente inativo ou em manutenção.', 409)

        cursor.execute("""
            UPDATE leitor_rfid
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL,
                manutencao_em = NULL,
                motivo_manutencao = NULL
            WHERE id_leitor = %s
        """, (id_leitor,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Leitor RFID reativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar leitor RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@leitores_bp.patch('/api/leitores-rfid/<int:id_leitor>/manutencao')
def colocar_leitor_em_manutencao(id_leitor):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Leitor RFID colocado em manutenção.')).strip()

    if motivo == '':
        motivo = 'Leitor RFID colocado em manutenção.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_leitor, status
            FROM leitor_rfid
            WHERE id_leitor = %s
        """, (id_leitor,))

        leitor = cursor.fetchone()

        if leitor is None:
            conexao.rollback()
            return resposta_erro('Leitor RFID não encontrado.', 404)

        if leitor['status'] == 'Manutenção':
            conexao.rollback()
            return resposta_erro('Leitor RFID já está em manutenção.', 409)

        cursor.execute("""
            UPDATE leitor_rfid
            SET
                status = 'Manutenção',
                inativado_em = NULL,
                motivo_inativacao = NULL,
                manutencao_em = NOW(),
                motivo_manutencao = %s
            WHERE id_leitor = %s
        """, (
            motivo,
            id_leitor
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Leitor RFID colocado em manutenção com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao colocar leitor RFID em manutenção: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()