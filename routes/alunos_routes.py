from flask import Blueprint, jsonify, request

from mysql.connector import IntegrityError, Error

from database import obter_conexao

alunos_bp = Blueprint('alunos_bp', __name__)

STATUS_ALUNO_VALIDOS = {'Ativo', 'Inativo'}

def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status

def validar_aluno(dados):

    nome = str(dados.get('nome', '')).strip()
    matricula = str(dados.get('matricula', '')).strip()
    email = str(dados.get('email', '')).strip().lower()
    data_nascimento = str(dados.get('data_nascimento', '')).strip()
    id_turma = dados.get('id_turma')
    tag = str(dados.get('tag', '')).strip()
    status = dados.get('status', 'Ativo')

    if email == '':
        email = None

    if data_nascimento == '':
        data_nascimento = None

    if not nome:
        return None, 'O nome do aluno é obrigatório.'

    if not matricula:
        return None, 'A matrícula do aluno é obrigatória.'

    if not id_turma:
        return None, 'A turma do aluno é obrigatória.'

    if not tag:
        return None, 'A tag RFID do aluno é obrigatória.'

    if status not in STATUS_ALUNO_VALIDOS:
        return None, 'Status inválido.'

    try:
        id_turma = int(id_turma)
    except (ValueError, TypeError):
        return None, 'Turma inválida.'

    return {
        'nome': nome,
        'matricula': matricula,
        'email': email,
        'data_nascimento': data_nascimento,
        'id_turma': id_turma,
        'tag': tag,
        'status': status
    }, None

@alunos_bp.get('/api/alunos')
def listar_alunos():

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)
    
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                a.id_aluno AS id,
                a.nome,
                a.matricula,
                a.email,
                DATE_FORMAT(a.data_nascimento, '%Y-%m-%d') AS data_nascimento,
                a.id_turma,
                a.status,
                DATE_FORMAT(a.inativado_em, '%Y-%m-%d %H:%i:%s') AS inativado_em,
                a.motivo_inativacao,
                t.nome AS turma,
                c.nome AS curso,
                tg.codigo AS tag
            FROM aluno a
            INNER JOIN turma t ON t.id_turma = a.id_turma
            INNER JOIN curso c ON c.id_curso = t.id_curso
            LEFT JOIN tag_rfid tg ON tg.id_tag = (
                SELECT tr.id_tag
                FROM tag_rfid tr
                WHERE tr.id_aluno = a.id_aluno
                ORDER BY tr.id_tag DESC
                LIMIT 1           
            )
            ORDER BY a.nome
        """)

        return jsonify(cursor.fetchall())
    
    except Error as erro:
        return resposta_erro(f'Erro ao listar alunos: {erro}', 500)
    
    finally:
        if cursor:
            cursor.close()

        conexao.close()

@alunos_bp.post('/api/alunos')
def cadastrar_aluno():
    
    dados = request.get_json(silent=True) or {}

    aluno, erro_validacao = validar_aluno(dados)

    if erro_validacao:
        return resposta_erro(erro_validacao)
    
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados', 500)
    
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        conexao.start_transaction()

        cursor.execute("""
            INSERT INTO aluno
                (nome, matricula, email, data_nascimento, id_turma, status)
            VALUES
                (%s, %s, %s, %s, %s, %s)

        """, (
            aluno['nome'],
            aluno['matricula'],
            aluno['email'],
            aluno['data_nascimento'],
            aluno['id_turma'],
            aluno['status']
        ))

        id_aluno = cursor.lastrowid

        status_tag = 'Ativa' if aluno['status'] == 'Ativo' else 'Inativa'

        cursor.execute("""
            INSERT INTO tag_rfid
                (codigo, id_aluno, status)
            VALUES
                (%s, %s, %s)
        """, (
            aluno['tag'],
            id_aluno,
            status_tag
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aluno cadastrado com sucesso.',
            'id_aluno': id_aluno
        }), 201
    
    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Matrícula, e-mail ou tag RFID já cadastrada', 409)
    
    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar aluno: {erro}', 500)

    finally:
        if cursor:
            cursor.close()
        
        conexao.close()

@alunos_bp.put('/api/alunos/<int:id_aluno>')
def atualizar_aluno(id_aluno):

    dados = request.get_json(silent=True) or {}
    aluno, erro_validacao = validar_aluno(dados)

    if erro_validacao:
        return resposta_erro(erro_validacao)

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_aluno
            FROM aluno
            WHERE id_aluno = %s
        """, (id_aluno,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Aluno não encontrado', 404)

        cursor.execute("""
            UPDATE aluno
            SET
                nome = %s,
                matricula = %s,
                email = %s,
                data_nascimento = %s,
                id_turma = %s,
                status = %s
            WHERE id_aluno = %s
        """, (
            aluno['nome'],
            aluno['matricula'],
            aluno['email'],
            aluno['data_nascimento'],
            aluno['id_turma'],
            aluno['status'],
            id_aluno
        ))

        cursor.execute("""
            SELECT id_tag
            FROM tag_rfid
            WHERE id_aluno = %s
            ORDER BY id_tag DESC
            LIMIT 1
        """, (id_aluno,))

        tag_atual = cursor.fetchone()
        status_tag = 'Ativa' if aluno['status'] == 'Ativo' else 'Inativa'

        if tag_atual:
            cursor.execute("""
                UPDATE tag_rfid
                SET
                    codigo = %s,
                    status = %s
                WHERE id_tag = %s
            """, (
                aluno['tag'],
                status_tag,
                tag_atual['id_tag']
            ))
        else:
            cursor.execute("""
                INSERT INTO tag_rfid
                    (codigo, id_aluno, status)
                VALUES
                    (%s, %s, %s)
            """, (
                aluno['tag'],
                id_aluno,
                status_tag
            ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aluno atualizado com sucesso.'
        })

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Matrícula, e-mail ou tag RFID já cadastrada', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar aluno: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@alunos_bp.patch('/api/alunos/<int:id_aluno>/inativar')
def inativar_aluno(id_aluno):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Aluno inativado pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Aluno inativado pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_aluno, status
            FROM aluno
            WHERE id_aluno = %s
        """, (id_aluno,))

        aluno = cursor.fetchone()

        if aluno is None:
            conexao.rollback()
            return resposta_erro('Aluno não encontrado', 404)

        if aluno['status'] == 'Inativo':
            conexao.rollback()
            return resposta_erro('Aluno já está inativo.', 409)

        cursor.execute("""
            UPDATE aluno
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s
            WHERE id_aluno = %s
        """, (
            motivo,
            id_aluno
        ))

        cursor.execute("""
            UPDATE tag_rfid
            SET
                status = 'Inativa',
                inativada_em = NOW()
            WHERE id_aluno = %s
            AND status = 'Ativa'
        """, (id_aluno,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aluno inativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar aluno: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@alunos_bp.patch('/api/alunos/<int:id_aluno>/reativar')
def reativar_aluno(id_aluno):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_aluno, status
            FROM aluno
            WHERE id_aluno = %s
        """, (id_aluno,))

        aluno = cursor.fetchone()

        if aluno is None:
            conexao.rollback()
            return resposta_erro('Aluno não encontrado', 404)

        if aluno['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Aluno já está ativo.', 409)

        cursor.execute("""
            UPDATE aluno
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL
            WHERE id_aluno = %s
        """, (id_aluno,))

        cursor.execute("""
            SELECT id_tag
            FROM tag_rfid
            WHERE id_aluno = %s
            ORDER BY id_tag DESC
            LIMIT 1
        """, (id_aluno,))

        tag_atual = cursor.fetchone()

        if tag_atual:
            cursor.execute("""
                UPDATE tag_rfid
                SET
                    status = 'Ativa',
                    inativada_em = NULL
                WHERE id_tag = %s
            """, (tag_atual['id_tag'],))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aluno reativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar aluno: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()
