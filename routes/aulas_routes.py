from datetime import datetime

from flask import Blueprint, jsonify, request, session
from mysql.connector import Error

from database import obter_conexao


aulas_bp = Blueprint('aulas', __name__)


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def obter_dados_json():
    return request.get_json(silent=True) or {}


def campo_obrigatorio(dados, campo):
    valor = dados.get(campo)

    if valor is None:
        return ''

    return str(valor).strip()


def converter_inteiro(valor, nome_campo):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(
            f'O campo {nome_campo} deve ser um número inteiro.'
        )


def validar_data(data_texto):
    try:
        datetime.strptime(data_texto, '%Y-%m-%d')
    except ValueError:
        raise ValueError(
            'A data da aula deve estar no formato AAAA-MM-DD.'
        )


def validar_horario(horario_texto, nome_campo):
    try:
        return datetime.strptime(
            horario_texto,
            '%H:%M'
        ).time()

    except ValueError:
        try:
            return datetime.strptime(
                horario_texto,
                '%H:%M:%S'
            ).time()

        except ValueError:
            raise ValueError(
                f'O campo {nome_campo} deve estar no formato HH:MM.'
            )


def verificar_recurso_ativo(
    cursor,
    tabela,
    campo_id,
    valor_id,
    status_esperado,
    mensagem_nao_encontrado,
    mensagem_indisponivel
):
    cursor.execute(
        f"""
            SELECT
                {campo_id},
                status
            FROM {tabela}
            WHERE {campo_id} = %s
            LIMIT 1
        """,
        (valor_id,)
    )

    registro = cursor.fetchone()

    if registro is None:
        raise ValueError(
            mensagem_nao_encontrado
        )

    if registro['status'] != status_esperado:
        raise ValueError(
            mensagem_indisponivel
        )

    return registro


def professor_tem_acesso_turma(
    cursor,
    id_professor,
    id_turma
):
    if not id_professor:
        return False

    cursor.execute("""
        SELECT id_professor_turma
        FROM professor_turma
        WHERE id_professor = %s
          AND id_turma = %s
          AND status = 'Ativo'
          AND funcao IN ('Professor', 'Auxiliar')
        LIMIT 1
    """, (
        id_professor,
        id_turma
    ))

    return cursor.fetchone() is not None


def verificar_vinculo_professor_turma(
    cursor,
    id_professor,
    id_turma
):
    cursor.execute("""
        SELECT
            funcao,
            status
        FROM professor_turma
        WHERE id_professor = %s
          AND id_turma = %s
          AND status = 'Ativo'
          AND funcao IN ('Professor', 'Auxiliar')
        LIMIT 1
    """, (
        id_professor,
        id_turma
    ))

    vinculo = cursor.fetchone()

    if vinculo is None:
        raise ValueError(
            'O professor selecionado não possui vínculo ativo '
            'como Professor ou Auxiliar nesta turma.'
        )

    return vinculo


def verificar_conflitos_aula(
    cursor,
    id_turma,
    id_professor,
    id_ambiente,
    data_aula,
    horario_inicio,
    horario_fim,
    id_aula_ignorar=None
):
    condicao_ignorar = ''
    parametros_ignorar = []

    if id_aula_ignorar is not None:
        condicao_ignorar = """
            AND a.id_aula <> %s
        """

        parametros_ignorar.append(
            id_aula_ignorar
        )

    parametros_base = [
        data_aula,
        horario_fim,
        horario_inicio
    ]

    cursor.execute(
        f"""
            SELECT
                a.id_aula,
                a.horario_inicio,
                a.horario_fim,
                t.nome AS turma
            FROM aula a
            INNER JOIN turma t
                ON t.id_turma = a.id_turma
            WHERE a.data_aula = %s
              AND a.status <> 'Cancelada'
              AND a.horario_inicio < %s
              AND a.horario_fim > %s
              AND a.id_turma = %s
              {condicao_ignorar}
            LIMIT 1
        """,
        parametros_base
        + [id_turma]
        + parametros_ignorar
    )

    conflito_turma = cursor.fetchone()

    if conflito_turma:
        raise ValueError(
            'A turma já possui outra aula '
            'nesse intervalo de horário.'
        )

    cursor.execute(
        f"""
            SELECT
                a.id_aula,
                a.horario_inicio,
                a.horario_fim,
                p.nome AS professor
            FROM aula a
            INNER JOIN professor p
                ON p.id_professor = a.id_professor
            WHERE a.data_aula = %s
              AND a.status <> 'Cancelada'
              AND a.horario_inicio < %s
              AND a.horario_fim > %s
              AND a.id_professor = %s
              {condicao_ignorar}
            LIMIT 1
        """,
        parametros_base
        + [id_professor]
        + parametros_ignorar
    )

    conflito_professor = cursor.fetchone()

    if conflito_professor:
        raise ValueError(
            'O professor selecionado já possui '
            'outra aula nesse intervalo de horário.'
        )

    cursor.execute(
        f"""
            SELECT
                a.id_aula,
                a.horario_inicio,
                a.horario_fim,
                amb.nome AS ambiente
            FROM aula a
            INNER JOIN ambiente amb
                ON amb.id_ambiente = a.id_ambiente
            WHERE a.data_aula = %s
              AND a.status <> 'Cancelada'
              AND a.horario_inicio < %s
              AND a.horario_fim > %s
              AND a.id_ambiente = %s
              {condicao_ignorar}
            LIMIT 1
        """,
        parametros_base
        + [id_ambiente]
        + parametros_ignorar
    )

    conflito_ambiente = cursor.fetchone()

    if conflito_ambiente:
        raise ValueError(
            'O ambiente selecionado já está ocupado '
            'por outra aula nesse intervalo de horário.'
        )


def montar_filtros_aulas():
    filtros = []
    parametros = []

    data_aula = request.args.get('data')
    id_turma = request.args.get('id_turma')
    id_professor = request.args.get('id_professor')
    id_ambiente = request.args.get('id_ambiente')
    status = request.args.get('status')

    if data_aula:
        filtros.append('a.data_aula = %s')
        parametros.append(data_aula)

    if id_turma:
        filtros.append('a.id_turma = %s')
        parametros.append(id_turma)

    if id_professor:
        filtros.append('a.id_professor = %s')
        parametros.append(id_professor)

    if id_ambiente:
        filtros.append('a.id_ambiente = %s')
        parametros.append(id_ambiente)

    if status:
        filtros.append('a.status = %s')
        parametros.append(status)

    where = ''

    if filtros:
        where = 'WHERE ' + ' AND '.join(filtros)

    return where, parametros


def consulta_base_aulas(where=''):
    return f"""
        SELECT
            a.id_aula AS id,
            a.id_turma,
            t.nome AS turma,
            a.id_professor,
            p.nome AS professor,
            a.id_ambiente,
            amb.nome AS ambiente,
            a.data_aula,
            a.horario_inicio,
            a.horario_fim,
            a.tolerancia_minutos,
            a.status,
            a.criado_em,
            a.atualizado_em,
            a.cancelada_em,
            a.motivo_cancelamento
        FROM aula a
        INNER JOIN turma t
            ON t.id_turma = a.id_turma
        INNER JOIN professor p
            ON p.id_professor = a.id_professor
        INNER JOIN ambiente amb
            ON amb.id_ambiente = a.id_ambiente
        {where}
    """


def formatar_aula(aula):
    return {
        'id': aula['id'],
        'id_turma': aula['id_turma'],
        'turma': aula['turma'],
        'id_professor': aula['id_professor'],
        'professor': aula['professor'],
        'id_ambiente': aula['id_ambiente'],
        'ambiente': aula['ambiente'],
        'data_aula': (
            aula['data_aula'].strftime('%Y-%m-%d')
            if aula['data_aula']
            else None
        ),
        'horario_inicio': (
            str(aula['horario_inicio'])
            if aula['horario_inicio']
            else None
        ),
        'horario_fim': (
            str(aula['horario_fim'])
            if aula['horario_fim']
            else None
        ),
        'tolerancia_minutos': aula['tolerancia_minutos'],
        'status': aula['status'],
        'criado_em': (
            aula['criado_em'].strftime('%Y-%m-%d %H:%M:%S')
            if aula['criado_em']
            else None
        ),
        'atualizado_em': (
            aula['atualizado_em'].strftime('%Y-%m-%d %H:%M:%S')
            if aula['atualizado_em']
            else None
        ),
        'cancelada_em': (
            aula['cancelada_em'].strftime('%Y-%m-%d %H:%M:%S')
            if aula['cancelada_em']
            else None
        ),
        'motivo_cancelamento': aula['motivo_cancelamento']
    }


def validar_dados_aula(dados):
    id_turma = converter_inteiro(
        campo_obrigatorio(dados, 'id_turma'),
        'id_turma'
    )

    id_professor = converter_inteiro(
        campo_obrigatorio(dados, 'id_professor'),
        'id_professor'
    )

    id_ambiente = converter_inteiro(
        campo_obrigatorio(dados, 'id_ambiente'),
        'id_ambiente'
    )

    data_aula = campo_obrigatorio(
        dados,
        'data_aula'
    )

    horario_inicio = campo_obrigatorio(
        dados,
        'horario_inicio'
    )

    horario_fim = campo_obrigatorio(
        dados,
        'horario_fim'
    )

    tolerancia_minutos = converter_inteiro(
        dados.get('tolerancia_minutos', 15),
        'tolerancia_minutos'
    )

    if not data_aula:
        raise ValueError(
            'A data da aula é obrigatória.'
        )

    if not horario_inicio:
        raise ValueError(
            'O horário de início é obrigatório.'
        )

    if not horario_fim:
        raise ValueError(
            'O horário de fim é obrigatório.'
        )

    validar_data(data_aula)

    horario_inicio_validado = validar_horario(
        horario_inicio,
        'horario_inicio'
    )

    horario_fim_validado = validar_horario(
        horario_fim,
        'horario_fim'
    )

    if horario_fim_validado <= horario_inicio_validado:
        raise ValueError(
            'O horário de fim deve ser maior que o horário de início.'
        )

    if tolerancia_minutos < 0 or tolerancia_minutos > 120:
        raise ValueError(
            'A tolerância deve estar entre 0 e 120 minutos.'
        )

    return {
        'id_turma': id_turma,
        'id_professor': id_professor,
        'id_ambiente': id_ambiente,
        'data_aula': data_aula,
        'horario_inicio': horario_inicio,
        'horario_fim': horario_fim,
        'tolerancia_minutos': tolerancia_minutos
    }


def validar_recursos_aula(
    cursor,
    id_turma,
    id_professor,
    id_ambiente
):
    verificar_recurso_ativo(
        cursor,
        'turma',
        'id_turma',
        id_turma,
        'Ativa',
        'Turma não encontrada.',
        'A turma selecionada não está ativa.'
    )

    verificar_recurso_ativo(
        cursor,
        'professor',
        'id_professor',
        id_professor,
        'Ativo',
        'Professor não encontrado.',
        'O professor selecionado não está ativo.'
    )

    verificar_recurso_ativo(
        cursor,
        'ambiente',
        'id_ambiente',
        id_ambiente,
        'Ativo',
        'Ambiente não encontrado.',
        'O ambiente selecionado não está ativo.'
    )

    verificar_vinculo_professor_turma(
        cursor,
        id_professor,
        id_turma
    )


@aulas_bp.get('/api/aulas')
def listar_aulas():
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        where, parametros = montar_filtros_aulas()

        usuario = session.get('usuario') or {}

        if usuario.get('perfil') == 'Professor':
            id_professor = usuario.get('id_professor')

            if not id_professor:
                return resposta_erro(
                    'Este usuário Professor não está vinculado '
                    'a um cadastro de professor.',
                    403
                )

            filtro_professor = """
                EXISTS (
                    SELECT 1
                    FROM professor_turma pt
                    WHERE pt.id_professor = %s
                      AND pt.id_turma = a.id_turma
                      AND pt.status = 'Ativo'
                      AND pt.funcao IN ('Professor', 'Auxiliar')
                )
            """

            if where:
                where += f" AND {filtro_professor}"
            else:
                where = f"WHERE {filtro_professor}"

            parametros.append(id_professor)

        cursor.execute(
            consulta_base_aulas(where)
            + """
                ORDER BY
                    a.data_aula DESC,
                    a.horario_inicio DESC
            """,
            parametros
        )

        aulas = cursor.fetchall()

        return jsonify({
            'aulas': [
                formatar_aula(aula)
                for aula in aulas
            ],
            'total': len(aulas)
        })

    except Error as erro:
        return resposta_erro(
            f'Erro ao listar aulas: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@aulas_bp.get('/api/aulas/<int:id_aula>')
def obter_aula(id_aula):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            consulta_base_aulas(
                'WHERE a.id_aula = %s'
            ),
            (id_aula,)
        )

        aula = cursor.fetchone()

        if aula is None:
            return resposta_erro(
                'Aula não encontrada.',
                404
            )

        usuario = session.get('usuario') or {}

        if usuario.get('perfil') == 'Professor':
            id_professor = usuario.get(
                'id_professor'
            )

            if not id_professor:
                return resposta_erro(
                    'Este usuário Professor não está vinculado '
                    'a um cadastro de professor.',
                    403
                )

            if not professor_tem_acesso_turma(
                cursor,
                id_professor,
                aula['id_turma']
            ):
                return resposta_erro(
                    'Você não possui acesso a esta aula.',
                    403
                )

        return jsonify({
            'aula': formatar_aula(aula)
        })

    except Error as erro:
        return resposta_erro(
            f'Erro ao buscar aula: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@aulas_bp.post('/api/aulas')
def criar_aula():
    dados = obter_dados_json()

    try:
        dados_aula = validar_dados_aula(
            dados
        )

    except ValueError as erro:
        return resposta_erro(
            str(erro)
        )

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        validar_recursos_aula(
            cursor,
            dados_aula['id_turma'],
            dados_aula['id_professor'],
            dados_aula['id_ambiente']
        )

        verificar_conflitos_aula(
            cursor=cursor,
            id_turma=dados_aula['id_turma'],
            id_professor=dados_aula['id_professor'],
            id_ambiente=dados_aula['id_ambiente'],
            data_aula=dados_aula['data_aula'],
            horario_inicio=dados_aula['horario_inicio'],
            horario_fim=dados_aula['horario_fim']
        )

        cursor.execute("""
            INSERT INTO aula (
                id_turma,
                id_professor,
                id_ambiente,
                data_aula,
                horario_inicio,
                horario_fim,
                tolerancia_minutos,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Programada'
            )
        """, (
            dados_aula['id_turma'],
            dados_aula['id_professor'],
            dados_aula['id_ambiente'],
            dados_aula['data_aula'],
            dados_aula['horario_inicio'],
            dados_aula['horario_fim'],
            dados_aula['tolerancia_minutos']
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aula cadastrada com sucesso.',
            'id_aula': cursor.lastrowid
        }), 201

    except ValueError as erro:
        return resposta_erro(
            str(erro)
        )

    except Error as erro:
        return resposta_erro(
            f'Erro ao cadastrar aula: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@aulas_bp.put('/api/aulas/<int:id_aula>')
def atualizar_aula(id_aula):
    dados = obter_dados_json()

    try:
        dados_aula = validar_dados_aula(
            dados
        )

    except ValueError as erro:
        return resposta_erro(
            str(erro)
        )

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id_aula,
                status
            FROM aula
            WHERE id_aula = %s
        """, (id_aula,))

        aula = cursor.fetchone()

        if aula is None:
            return resposta_erro(
                'Aula não encontrada.',
                404
            )

        if aula['status'] != 'Programada':
            return resposta_erro(
                'Somente aulas programadas podem ser editadas.',
                409
            )

        validar_recursos_aula(
            cursor,
            dados_aula['id_turma'],
            dados_aula['id_professor'],
            dados_aula['id_ambiente']
        )

        verificar_conflitos_aula(
            cursor=cursor,
            id_turma=dados_aula['id_turma'],
            id_professor=dados_aula['id_professor'],
            id_ambiente=dados_aula['id_ambiente'],
            data_aula=dados_aula['data_aula'],
            horario_inicio=dados_aula['horario_inicio'],
            horario_fim=dados_aula['horario_fim'],
            id_aula_ignorar=id_aula
        )

        cursor.execute("""
            UPDATE aula
            SET
                id_turma = %s,
                id_professor = %s,
                id_ambiente = %s,
                data_aula = %s,
                horario_inicio = %s,
                horario_fim = %s,
                tolerancia_minutos = %s,
                atualizado_em = NOW()
            WHERE id_aula = %s
        """, (
            dados_aula['id_turma'],
            dados_aula['id_professor'],
            dados_aula['id_ambiente'],
            dados_aula['data_aula'],
            dados_aula['horario_inicio'],
            dados_aula['horario_fim'],
            dados_aula['tolerancia_minutos'],
            id_aula
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aula atualizada com sucesso.'
        })

    except ValueError as erro:
        return resposta_erro(
            str(erro)
        )

    except Error as erro:
        return resposta_erro(
            f'Erro ao atualizar aula: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@aulas_bp.patch('/api/aulas/<int:id_aula>/iniciar')
def iniciar_aula(id_aula):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT
                id_aula,
                id_turma,
                status
            FROM aula
            WHERE id_aula = %s
        """, (id_aula,))

        aula = cursor.fetchone()

        if aula is None:
            conexao.rollback()

            return resposta_erro(
                'Aula não encontrada.',
                404
            )

        usuario = session.get('usuario') or {}

        if usuario.get('perfil') == 'Professor':
            id_professor = usuario.get(
                'id_professor'
            )

            if not id_professor:
                conexao.rollback()

                return resposta_erro(
                    'Este usuário Professor não está vinculado '
                    'a um cadastro de professor.',
                    403
                )

            if not professor_tem_acesso_turma(
                cursor,
                id_professor,
                aula['id_turma']
            ):
                conexao.rollback()

                return resposta_erro(
                    'Você não possui permissão para iniciar '
                    'uma aula desta turma.',
                    403
                )

        if aula['status'] == 'Cancelada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível iniciar uma aula cancelada.'
            )

        if aula['status'] == 'Finalizada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível iniciar uma aula finalizada.'
            )

        if aula['status'] == 'Em andamento':
            conexao.rollback()

            return resposta_erro(
                'A aula já está em andamento.',
                409
            )

        if aula['status'] != 'Programada':
            conexao.rollback()

            return resposta_erro(
                'A aula não está em um estado válido para ser iniciada.'
            )

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM presenca
            WHERE id_aula = %s
        """, (id_aula,))

        resultado = cursor.fetchone()

        if resultado['total'] == 0:
            conexao.rollback()

            return resposta_erro(
                'A chamada deve ser gerada antes de iniciar a aula.'
            )

        cursor.execute("""
            UPDATE aula
            SET
                status = 'Em andamento',
                atualizado_em = NOW()
            WHERE id_aula = %s
        """, (id_aula,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aula iniciada com sucesso.'
        })

    except Error as erro:
        conexao.rollback()

        return resposta_erro(
            f'Erro ao iniciar aula: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@aulas_bp.patch('/api/aulas/<int:id_aula>/finalizar')
def finalizar_aula(id_aula):
    return resposta_erro(
        'A aula deve ser finalizada através da chamada '
        'em /api/chamadas/<id_aula>/finalizar.',
        400
    )


@aulas_bp.patch('/api/aulas/<int:id_aula>/cancelar')
def cancelar_aula(id_aula):
    dados = obter_dados_json()

    motivo = str(
        dados.get('motivo', '')
    ).strip()

    if not motivo:
        return resposta_erro(
            'O motivo do cancelamento é obrigatório.'
        )

    if len(motivo) > 255:
        return resposta_erro(
            'O motivo do cancelamento deve possuir no máximo 255 caracteres.'
        )

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        conexao.start_transaction()

        cursor.execute("""
            SELECT
                id_aula,
                status
            FROM aula
            WHERE id_aula = %s
        """, (id_aula,))

        aula = cursor.fetchone()

        if aula is None:
            conexao.rollback()

            return resposta_erro(
                'Aula não encontrada.',
                404
            )

        if aula['status'] == 'Cancelada':
            conexao.rollback()

            return resposta_erro(
                'A aula já está cancelada.',
                409
            )

        if aula['status'] == 'Em andamento':
            conexao.rollback()

            return resposta_erro(
                'Não é possível cancelar uma aula que já está em andamento.'
            )

        if aula['status'] == 'Finalizada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível cancelar uma aula finalizada.'
            )

        if aula['status'] != 'Programada':
            conexao.rollback()

            return resposta_erro(
                'A aula não está em um estado válido para cancelamento.'
            )

        cursor.execute("""
            UPDATE aula
            SET
                status = 'Cancelada',
                cancelada_em = NOW(),
                motivo_cancelamento = %s,
                atualizado_em = NOW()
            WHERE id_aula = %s
        """, (
            motivo,
            id_aula
        ))

        cursor.execute("""
            UPDATE presenca
            SET
                observacao = 'Chamada sem efeito devido ao cancelamento da aula.',
                atualizado_em = NOW()
            WHERE id_aula = %s
              AND status = 'Pendente'
        """, (id_aula,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Aula cancelada com sucesso.',
            'id_aula': id_aula,
            'motivo': motivo
        })

    except Error as erro:
        conexao.rollback()

        return resposta_erro(
            f'Erro ao cancelar aula: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()
