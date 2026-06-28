from flask import Blueprint, jsonify, request
from mysql.connector import IntegrityError, Error
from database import obter_conexao

academico_bp = Blueprint('academico_bp', __name__)

STATUS_CURSO_VALIDOS = {'Ativo', 'Inativo'}
STATUS_TURMA_VALIDOS = {'Ativa', 'Inativa', 'Encerrada'}
PERIODOS_VALIDOS = {'Manhã', 'Tarde', 'Noite', 'Integral'}
FUNCOES_PROFESSOR_TURMA_VALIDAS = {'Responsável', 'Professor', 'Auxiliar'}
STATUS_VINCULO_VALIDOS = {'Ativo', 'Inativo'}

def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status

def validar_curso(dados):
    nome = str(dados.get('nome', '')).strip()
    codigo = str(dados.get('codigo', '')).strip().upper()
    status = dados.get('status', 'Ativo')

    if not nome:
        return None, 'O nome do curso é obrigatório.'

    if not codigo:
        return None, 'O código do curso é obrigatório.'

    if status not in STATUS_CURSO_VALIDOS:
        return None, 'Status inválido.'

    return {
        'nome': nome,
        'codigo': codigo,
        'status': status
    }, None

def validar_turma(dados):
    nome = str(dados.get('nome', '')).strip()
    id_curso = dados.get('id_curso')
    periodo = dados.get('periodo', '')
    ano_letivo = dados.get('ano_letivo')
    semestre = dados.get('semestre')
    status = dados.get('status', 'Ativa')

    if not nome:
        return None, 'O nome da turma é obrigatório.'

    if not id_curso:
        return None, 'O curso da turma é obrigatório.'

    if periodo not in PERIODOS_VALIDOS:
        return None, 'Período inválido.'

    if not ano_letivo:
        return None, 'O ano letivo é obrigatório.'

    if not semestre:
        return None, 'O semestre é obrigatório.'

    if status not in STATUS_TURMA_VALIDOS:
        return None, 'Status inválido.'

    try:
        id_curso = int(id_curso)
    except (ValueError, TypeError):
        return None, 'Curso inválido.'

    try:
        ano_letivo = int(ano_letivo)
    except (ValueError, TypeError):
        return None, 'Ano letivo inválido.'

    try:
        semestre = int(semestre)
    except (ValueError, TypeError):
        return None, 'Semestre inválido.'

    if ano_letivo < 2000 or ano_letivo > 2100:
        return None, 'Ano letivo inválido.'

    if semestre not in {1, 2}:
        return None, 'Semestre inválido.'

    return {
        'nome': nome,
        'id_curso': id_curso,
        'periodo': periodo,
        'ano_letivo': ano_letivo,
        'semestre': semestre,
        'status': status
    }, None

def validar_professor_turma(dados):
    id_professor = dados.get('id_professor')
    id_turma = dados.get('id_turma')
    funcao = dados.get('funcao', 'Professor')
    status = dados.get('status', 'Ativo')

    if not id_professor:
        return None, 'O professor é obrigatório.'

    if not id_turma:
        return None, 'A turma é obrigatória.'

    if funcao not in FUNCOES_PROFESSOR_TURMA_VALIDAS:
        return None, 'Função inválida.'

    if status not in STATUS_VINCULO_VALIDOS:
        return None, 'Status inválido.'

    try:
        id_professor = int(id_professor)
    except (ValueError, TypeError):
        return None, 'Professor inválido.'

    try:
        id_turma = int(id_turma)
    except (ValueError, TypeError):
        return None, 'Turma inválida.'

    return {
        'id_professor': id_professor,
        'id_turma': id_turma,
        'funcao': funcao,
        'status': status
    }, None

@academico_bp.get('/api/cursos')
def listar_cursos():
    status = request.args.get('status', 'Todos')

    if status != 'Todos' and status not in STATUS_CURSO_VALIDOS:
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
                    id_curso AS id,
                    nome,
                    codigo,
                    status,
                    CAST(inativado_em AS CHAR) AS inativado_em,
                    motivo_inativacao
                FROM curso
                ORDER BY nome
            """)
        else:
            cursor.execute("""
                SELECT
                    id_curso AS id,
                    nome,
                    codigo,
                    status,
                    CAST(inativado_em AS CHAR) AS inativado_em,
                    motivo_inativacao
                FROM curso
                WHERE status = %s
                ORDER BY nome
            """, (status,))

        return jsonify(cursor.fetchall())

    except Error as erro:
        return resposta_erro(f'Erro ao listar cursos: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.post('/api/cursos')
def cadastrar_curso():
    dados = request.get_json(silent=True) or {}
    curso, erro_validacao = validar_curso(dados)

    if erro_validacao:
        return resposta_erro(erro_validacao)

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO curso
                (nome, codigo, status)
            VALUES
                (%s, %s, %s)
        """, (
            curso['nome'],
            curso['codigo'],
            curso['status']
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Curso cadastrado com sucesso.',
            'id_curso': cursor.lastrowid
        }), 201

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Código de curso já cadastrado.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar curso: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.put('/api/cursos/<int:id_curso>')
def atualizar_curso(id_curso):
    dados = request.get_json(silent=True) or {}
    curso, erro_validacao = validar_curso(dados)

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
            SELECT id_curso
            FROM curso
            WHERE id_curso = %s
        """, (id_curso,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Curso não encontrado.', 404)

        cursor.execute("""
            UPDATE curso
            SET
                nome = %s,
                codigo = %s,
                status = %s
            WHERE id_curso = %s
        """, (
            curso['nome'],
            curso['codigo'],
            curso['status'],
            id_curso
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Curso atualizado com sucesso.'
        })

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Código de curso já cadastrado.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar curso: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.patch('/api/cursos/<int:id_curso>/inativar')
def inativar_curso(id_curso):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Curso inativado pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Curso inativado pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_curso, status
            FROM curso
            WHERE id_curso = %s
        """, (id_curso,))

        curso = cursor.fetchone()

        if curso is None:
            conexao.rollback()
            return resposta_erro('Curso não encontrado.', 404)

        if curso['status'] == 'Inativo':
            conexao.rollback()
            return resposta_erro('Curso já está inativo.', 409)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM turma
            WHERE id_curso = %s
            AND status = 'Ativa'
        """, (id_curso,))

        resultado = cursor.fetchone()

        if resultado['total'] > 0:
            conexao.rollback()
            return resposta_erro('Não é possível inativar um curso com turmas ativas.', 409)

        cursor.execute("""
            UPDATE curso
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s
            WHERE id_curso = %s
        """, (
            motivo,
            id_curso
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Curso inativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar curso: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.patch('/api/cursos/<int:id_curso>/reativar')
def reativar_curso(id_curso):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_curso, status
            FROM curso
            WHERE id_curso = %s
        """, (id_curso,))

        curso = cursor.fetchone()

        if curso is None:
            conexao.rollback()
            return resposta_erro('Curso não encontrado.', 404)

        if curso['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Curso já está ativo.', 409)

        cursor.execute("""
            UPDATE curso
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL
            WHERE id_curso = %s
        """, (id_curso,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Curso reativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar curso: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.get('/api/turmas')
def listar_turmas():
    status = request.args.get('status', 'Ativa')

    if status != 'Todos' and status not in STATUS_TURMA_VALIDOS:
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
                    t.id_turma AS id,
                    t.id_turma,
                    t.nome,
                    t.id_curso,
                    t.periodo,
                    t.ano_letivo,
                    t.semestre,
                    t.status,
                    CAST(t.inativada_em AS CHAR) AS inativada_em,
                    t.motivo_inativacao,
                    CAST(t.encerrada_em AS CHAR) AS encerrada_em,
                    t.motivo_encerramento,
                    c.nome AS curso,
                    c.codigo AS codigo_curso
                FROM turma t
                INNER JOIN curso c ON c.id_curso = t.id_curso
                ORDER BY c.nome, t.nome
            """)
        else:
            cursor.execute("""
                SELECT
                    t.id_turma AS id,
                    t.id_turma,
                    t.nome,
                    t.id_curso,
                    t.periodo,
                    t.ano_letivo,
                    t.semestre,
                    t.status,
                    CAST(t.inativada_em AS CHAR) AS inativada_em,
                    t.motivo_inativacao,
                    CAST(t.encerrada_em AS CHAR) AS encerrada_em,
                    t.motivo_encerramento,
                    c.nome AS curso,
                    c.codigo AS codigo_curso
                FROM turma t
                INNER JOIN curso c ON c.id_curso = t.id_curso
                WHERE t.status = %s
                ORDER BY c.nome, t.nome
            """, (status,))

        return jsonify(cursor.fetchall())

    except Error as erro:
        return resposta_erro(f'Erro ao listar turmas: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.post('/api/turmas')
def cadastrar_turma():
    dados = request.get_json(silent=True) or {}
    turma, erro_validacao = validar_turma(dados)

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
            SELECT id_curso, status
            FROM curso
            WHERE id_curso = %s
        """, (turma['id_curso'],))

        curso = cursor.fetchone()

        if curso is None:
            conexao.rollback()
            return resposta_erro('Curso não encontrado.', 404)

        if curso['status'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível cadastrar turma em curso inativo.', 409)

        cursor.execute("""
            INSERT INTO turma
                (nome, id_curso, periodo, ano_letivo, semestre, status)
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """, (
            turma['nome'],
            turma['id_curso'],
            turma['periodo'],
            turma['ano_letivo'],
            turma['semestre'],
            turma['status']
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Turma cadastrada com sucesso.',
            'id_turma': cursor.lastrowid
        }), 201

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Não foi possível cadastrar a turma. Verifique os dados informados.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar turma: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.put('/api/turmas/<int:id_turma>')
def atualizar_turma(id_turma):
    dados = request.get_json(silent=True) or {}
    turma, erro_validacao = validar_turma(dados)

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
            SELECT id_turma
            FROM turma
            WHERE id_turma = %s
        """, (id_turma,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Turma não encontrada.', 404)

        cursor.execute("""
            SELECT id_curso, status
            FROM curso
            WHERE id_curso = %s
        """, (turma['id_curso'],))

        curso = cursor.fetchone()

        if curso is None:
            conexao.rollback()
            return resposta_erro('Curso não encontrado.', 404)

        if curso['status'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível vincular turma a curso inativo.', 409)

        cursor.execute("""
            UPDATE turma
            SET
                nome = %s,
                id_curso = %s,
                periodo = %s,
                ano_letivo = %s,
                semestre = %s,
                status = %s
            WHERE id_turma = %s
        """, (
            turma['nome'],
            turma['id_curso'],
            turma['periodo'],
            turma['ano_letivo'],
            turma['semestre'],
            turma['status'],
            id_turma
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Turma atualizada com sucesso.'
        })

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Não foi possível atualizar a turma. Verifique os dados informados.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar turma: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.patch('/api/turmas/<int:id_turma>/inativar')
def inativar_turma(id_turma):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Turma inativada pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Turma inativada pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_turma, status
            FROM turma
            WHERE id_turma = %s
        """, (id_turma,))

        turma = cursor.fetchone()

        if turma is None:
            conexao.rollback()
            return resposta_erro('Turma não encontrada.', 404)

        if turma['status'] == 'Inativa':
            conexao.rollback()
            return resposta_erro('Turma já está inativa.', 409)

        cursor.execute("""
            UPDATE turma
            SET
                status = 'Inativa',
                inativada_em = NOW(),
                motivo_inativacao = %s
            WHERE id_turma = %s
        """, (
            motivo,
            id_turma
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Turma inativada com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar turma: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.patch('/api/turmas/<int:id_turma>/reativar')
def reativar_turma(id_turma):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT t.id_turma, t.status, c.status AS status_curso
            FROM turma t
            INNER JOIN curso c ON c.id_curso = t.id_curso
            WHERE t.id_turma = %s
        """, (id_turma,))

        turma = cursor.fetchone()

        if turma is None:
            conexao.rollback()
            return resposta_erro('Turma não encontrada.', 404)

        if turma['status'] == 'Ativa':
            conexao.rollback()
            return resposta_erro('Turma já está ativa.', 409)

        if turma['status_curso'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível reativar turma de curso inativo.', 409)

        cursor.execute("""
            UPDATE turma
            SET
                status = 'Ativa',
                inativada_em = NULL,
                motivo_inativacao = NULL,
                encerrada_em = NULL,
                motivo_encerramento = NULL
            WHERE id_turma = %s
        """, (id_turma,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Turma reativada com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar turma: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.patch('/api/turmas/<int:id_turma>/encerrar')
def encerrar_turma(id_turma):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Turma encerrada pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Turma encerrada pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_turma, status
            FROM turma
            WHERE id_turma = %s
        """, (id_turma,))

        turma = cursor.fetchone()

        if turma is None:
            conexao.rollback()
            return resposta_erro('Turma não encontrada.', 404)

        if turma['status'] == 'Encerrada':
            conexao.rollback()
            return resposta_erro('Turma já está encerrada.', 409)

        cursor.execute("""
            UPDATE turma
            SET
                status = 'Encerrada',
                encerrada_em = NOW(),
                motivo_encerramento = %s
            WHERE id_turma = %s
        """, (
            motivo,
            id_turma
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Turma encerrada com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao encerrar turma: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()

@academico_bp.get('/api/professor-turma')
def listar_professor_turma():
    status = request.args.get('status', 'Todos')

    if status != 'Todos' and status not in STATUS_VINCULO_VALIDOS:
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
                    pt.id_professor_turma AS id,
                    pt.id_professor,
                    pt.id_turma,
                    pt.funcao,
                    pt.status,
                    CAST(pt.criado_em AS CHAR) AS criado_em,
                    CAST(pt.inativado_em AS CHAR) AS inativado_em,
                    pt.motivo_inativacao,
                    p.nome AS professor,
                    p.email AS email_professor,
                    p.registro_professor,
                    t.nome AS turma,
                    t.periodo,
                    t.ano_letivo,
                    t.semestre,
                    c.nome AS curso,
                    c.codigo AS codigo_curso
                FROM professor_turma pt
                INNER JOIN professor p ON p.id_professor = pt.id_professor
                INNER JOIN turma t ON t.id_turma = pt.id_turma
                INNER JOIN curso c ON c.id_curso = t.id_curso
                ORDER BY p.nome, t.nome
            """)
        else:
            cursor.execute("""
                SELECT
                    pt.id_professor_turma AS id,
                    pt.id_professor,
                    pt.id_turma,
                    pt.funcao,
                    pt.status,
                    CAST(pt.criado_em AS CHAR) AS criado_em,
                    CAST(pt.inativado_em AS CHAR) AS inativado_em,
                    pt.motivo_inativacao,
                    p.nome AS professor,
                    p.email AS email_professor,
                    p.registro_professor,
                    t.nome AS turma,
                    t.periodo,
                    t.ano_letivo,
                    t.semestre,
                    c.nome AS curso,
                    c.codigo AS codigo_curso
                FROM professor_turma pt
                INNER JOIN professor p ON p.id_professor = pt.id_professor
                INNER JOIN turma t ON t.id_turma = pt.id_turma
                INNER JOIN curso c ON c.id_curso = t.id_curso
                WHERE pt.status = %s
                ORDER BY p.nome, t.nome
            """, (status,))

        return jsonify(cursor.fetchall())

    except Error as erro:
        return resposta_erro(f'Erro ao listar vínculos: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@academico_bp.post('/api/professor-turma')
def cadastrar_professor_turma():
    dados = request.get_json(silent=True) or {}
    vinculo, erro_validacao = validar_professor_turma(dados)

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
            SELECT id_professor, status
            FROM professor
            WHERE id_professor = %s
        """, (vinculo['id_professor'],))

        professor = cursor.fetchone()

        if professor is None:
            conexao.rollback()
            return resposta_erro('Professor não encontrado.', 404)

        if professor['status'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível vincular professor inativo.', 409)

        cursor.execute("""
            SELECT id_turma, status
            FROM turma
            WHERE id_turma = %s
        """, (vinculo['id_turma'],))

        turma = cursor.fetchone()

        if turma is None:
            conexao.rollback()
            return resposta_erro('Turma não encontrada.', 404)

        if turma['status'] != 'Ativa':
            conexao.rollback()
            return resposta_erro('Não é possível vincular turma inativa ou encerrada.', 409)

        cursor.execute("""
            SELECT id_professor_turma, status
            FROM professor_turma
            WHERE id_professor = %s
            AND id_turma = %s
        """, (
            vinculo['id_professor'],
            vinculo['id_turma']
        ))

        vinculo_existente = cursor.fetchone()

        if vinculo_existente and vinculo_existente['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Este professor já está vinculado a esta turma.', 409)

        if vinculo_existente and vinculo_existente['status'] == 'Inativo':
            cursor.execute("""
                UPDATE professor_turma
                SET
                    funcao = %s,
                    status = 'Ativo',
                    inativado_em = NULL,
                    motivo_inativacao = NULL
                WHERE id_professor_turma = %s
            """, (
                vinculo['funcao'],
                vinculo_existente['id_professor_turma']
            ))

            conexao.commit()

            return jsonify({
                'mensagem': 'Vínculo reativado com sucesso.',
                'id_professor_turma': vinculo_existente['id_professor_turma']
            })

        cursor.execute("""
            INSERT INTO professor_turma
                (id_professor, id_turma, funcao, status)
            VALUES
                (%s, %s, %s, %s)
        """, (
            vinculo['id_professor'],
            vinculo['id_turma'],
            vinculo['funcao'],
            vinculo['status']
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Vínculo cadastrado com sucesso.',
            'id_professor_turma': cursor.lastrowid
        }), 201

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Este vínculo já existe.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar vínculo: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@academico_bp.put('/api/professor-turma/<int:id_professor_turma>')
def atualizar_professor_turma(id_professor_turma):
    dados = request.get_json(silent=True) or {}
    vinculo, erro_validacao = validar_professor_turma(dados)

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
            SELECT id_professor_turma
            FROM professor_turma
            WHERE id_professor_turma = %s
        """, (id_professor_turma,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Vínculo não encontrado.', 404)

        cursor.execute("""
            SELECT id_professor, status
            FROM professor
            WHERE id_professor = %s
        """, (vinculo['id_professor'],))

        professor = cursor.fetchone()

        if professor is None:
            conexao.rollback()
            return resposta_erro('Professor não encontrado.', 404)

        if professor['status'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível vincular professor inativo.', 409)

        cursor.execute("""
            SELECT id_turma, status
            FROM turma
            WHERE id_turma = %s
        """, (vinculo['id_turma'],))

        turma = cursor.fetchone()

        if turma is None:
            conexao.rollback()
            return resposta_erro('Turma não encontrada.', 404)

        if turma['status'] != 'Ativa':
            conexao.rollback()
            return resposta_erro('Não é possível vincular turma inativa ou encerrada.', 409)

        cursor.execute("""
            SELECT id_professor_turma
            FROM professor_turma
            WHERE id_professor = %s
            AND id_turma = %s
            AND id_professor_turma <> %s
        """, (
            vinculo['id_professor'],
            vinculo['id_turma'],
            id_professor_turma
        ))

        if cursor.fetchone():
            conexao.rollback()
            return resposta_erro('Este professor já está vinculado a esta turma.', 409)

        cursor.execute("""
            UPDATE professor_turma
            SET
                id_professor = %s,
                id_turma = %s,
                funcao = %s,
                status = %s
            WHERE id_professor_turma = %s
        """, (
            vinculo['id_professor'],
            vinculo['id_turma'],
            vinculo['funcao'],
            vinculo['status'],
            id_professor_turma
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Vínculo atualizado com sucesso.'
        })

    except IntegrityError:
        conexao.rollback()
        return resposta_erro('Este vínculo já existe.', 409)

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar vínculo: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@academico_bp.patch('/api/professor-turma/<int:id_professor_turma>/inativar')
def inativar_professor_turma(id_professor_turma):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Vínculo inativado pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Vínculo inativado pelo sistema.'

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT id_professor_turma, status
            FROM professor_turma
            WHERE id_professor_turma = %s
        """, (id_professor_turma,))

        vinculo = cursor.fetchone()

        if vinculo is None:
            conexao.rollback()
            return resposta_erro('Vínculo não encontrado.', 404)

        if vinculo['status'] == 'Inativo':
            conexao.rollback()
            return resposta_erro('Vínculo já está inativo.', 409)

        cursor.execute("""
            UPDATE professor_turma
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s
            WHERE id_professor_turma = %s
        """, (
            motivo,
            id_professor_turma
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Vínculo inativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar vínculo: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@academico_bp.patch('/api/professor-turma/<int:id_professor_turma>/reativar')
def reativar_professor_turma(id_professor_turma):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT
                pt.id_professor_turma,
                pt.status,
                p.status AS status_professor,
                t.status AS status_turma
            FROM professor_turma pt
            INNER JOIN professor p ON p.id_professor = pt.id_professor
            INNER JOIN turma t ON t.id_turma = pt.id_turma
            WHERE pt.id_professor_turma = %s
        """, (id_professor_turma,))

        vinculo = cursor.fetchone()

        if vinculo is None:
            conexao.rollback()
            return resposta_erro('Vínculo não encontrado.', 404)

        if vinculo['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Vínculo já está ativo.', 409)

        if vinculo['status_professor'] != 'Ativo':
            conexao.rollback()
            return resposta_erro('Não é possível reativar vínculo de professor inativo.', 409)

        if vinculo['status_turma'] != 'Ativa':
            conexao.rollback()
            return resposta_erro('Não é possível reativar vínculo de turma inativa ou encerrada.', 409)

        cursor.execute("""
            UPDATE professor_turma
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL
            WHERE id_professor_turma = %s
        """, (id_professor_turma,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Vínculo reativado com sucesso.'
        })

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar vínculo: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()