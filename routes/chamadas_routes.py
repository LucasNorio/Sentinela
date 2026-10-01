from flask import Blueprint, jsonify, session
from mysql.connector import Error

from database import obter_conexao


chamadas_bp = Blueprint('chamadas', __name__)

ANTECEDENCIA_MINUTOS = 15


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def formatar_data(valor):
    if valor is None:
        return None

    return valor.strftime('%Y-%m-%d')


def formatar_data_hora(valor):
    if valor is None:
        return None

    return valor.strftime('%Y-%m-%d %H:%M:%S')


def formatar_horario(valor):
    if valor is None:
        return None

    return str(valor)


def validar_acesso_professor_aula(
    cursor,
    aula
):
    usuario = session.get('usuario') or {}

    if usuario.get('perfil') != 'Professor':
        return None

    id_professor = usuario.get('id_professor')

    if not id_professor:
        return (
            'Este usuário Professor não está vinculado '
            'a um cadastro de professor.'
        )

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
        aula['id_turma']
    ))

    vinculo = cursor.fetchone()

    if vinculo is None:
        return (
            'Você não possui permissão para acessar '
            'a chamada desta turma.'
        )

    return None


def buscar_aula(cursor, id_aula):
    cursor.execute("""
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
        WHERE a.id_aula = %s
    """, (id_aula,))

    return cursor.fetchone()


def formatar_aula(aula):
    return {
        'id': aula['id'],
        'id_turma': aula['id_turma'],
        'turma': aula['turma'],
        'id_professor': aula['id_professor'],
        'professor': aula['professor'],
        'id_ambiente': aula['id_ambiente'],
        'ambiente': aula['ambiente'],
        'data_aula': formatar_data(
            aula['data_aula']
        ),
        'horario_inicio': formatar_horario(
            aula['horario_inicio']
        ),
        'horario_fim': formatar_horario(
            aula['horario_fim']
        ),
        'tolerancia_minutos': aula['tolerancia_minutos'],
        'status': aula['status'],
        'criado_em': formatar_data_hora(
            aula['criado_em']
        ),
        'atualizado_em': formatar_data_hora(
            aula['atualizado_em']
        ),
        'cancelada_em': formatar_data_hora(
            aula['cancelada_em']
        ),
        'motivo_cancelamento': aula['motivo_cancelamento']
    }


def formatar_presenca(presenca):
    return {
        'id': presenca['id'],
        'id_aula': presenca['id_aula'],
        'id_aluno': presenca['id_aluno'],
        'aluno': presenca['aluno'],
        'matricula': presenca['matricula'],
        'status_aluno': presenca['status_aluno'],
        'id_registro_rfid': presenca['id_registro_rfid'],
        'codigo_tag': presenca['codigo_tag'],
        'status_tag': presenca['status_tag'],
        'status': presenca['status'],
        'origem': presenca['origem'],
        'horario_detectado': formatar_data_hora(
            presenca['horario_detectado']
        ),
        'observacao': presenca['observacao'],
        'criado_em': formatar_data_hora(
            presenca['criado_em']
        ),
        'atualizado_em': formatar_data_hora(
            presenca['atualizado_em']
        )
    }


def validar_aula_e_acesso(
    cursor,
    id_aula
):
    aula = buscar_aula(
        cursor,
        id_aula
    )

    if aula is None:
        return None, resposta_erro(
            'Aula não encontrada.',
            404
        )

    erro_acesso = validar_acesso_professor_aula(
        cursor,
        aula
    )

    if erro_acesso:
        return None, resposta_erro(
            erro_acesso,
            403
        )

    return aula, None


@chamadas_bp.get('/api/chamadas/<int:id_aula>')
def obter_chamada(id_aula):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        aula, erro = validar_aula_e_acesso(
            cursor,
            id_aula
        )

        if erro:
            return erro

        cursor.execute("""
            SELECT
                pr.id_presenca AS id,
                pr.id_aula,
                pr.id_aluno,
                al.nome AS aluno,
                al.matricula,
                al.status AS status_aluno,
                pr.id_registro_rfid,
                tag.codigo AS codigo_tag,
                tag.status AS status_tag,
                pr.status,
                pr.origem,
                pr.horario_detectado,
                pr.observacao,
                pr.criado_em,
                pr.atualizado_em
            FROM presenca pr
            INNER JOIN aluno al
                ON al.id_aluno = pr.id_aluno
            LEFT JOIN tag_rfid tag
                ON tag.id_aluno = al.id_aluno
            WHERE pr.id_aula = %s
            ORDER BY al.nome ASC
        """, (id_aula,))

        presencas = cursor.fetchall()

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM presenca
            WHERE id_aula = %s
            GROUP BY status
        """, (id_aula,))

        resumo_status = cursor.fetchall()

        resumo = {
            'Pendente': 0,
            'Presente': 0,
            'Atrasado': 0,
            'Ausente': 0,
            'Justificado': 0
        }

        for item in resumo_status:
            resumo[item['status']] = item['total']

        return jsonify({
            'aula': formatar_aula(aula),
            'presencas': [
                formatar_presenca(presenca)
                for presenca in presencas
            ],
            'resumo': resumo,
            'total': len(presencas)
        })

    except Error as erro:
        return resposta_erro(
            f'Erro ao buscar chamada: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@chamadas_bp.post('/api/chamadas/<int:id_aula>/gerar')
def gerar_chamada(id_aula):
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

        aula, erro = validar_aula_e_acesso(
            cursor,
            id_aula
        )

        if erro:
            conexao.rollback()
            return erro

        if aula['status'] == 'Cancelada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível gerar chamada para uma aula cancelada.'
            )

        if aula['status'] == 'Finalizada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível gerar chamada para uma aula finalizada.'
            )

        if aula['status'] not in {
            'Programada',
            'Em andamento'
        }:
            conexao.rollback()

            return resposta_erro(
                'A aula não está em um estado válido para gerar chamada.'
            )

        cursor.execute("""
            SELECT
                id_aluno
            FROM aluno
            WHERE id_turma = %s
              AND status = 'Ativo'
            ORDER BY nome ASC
        """, (aula['id_turma'],))

        alunos = cursor.fetchall()

        if not alunos:
            conexao.rollback()

            return resposta_erro(
                'Não há alunos ativos vinculados à turma desta aula.'
            )

        presencas_criadas = 0

        for aluno in alunos:
            cursor.execute("""
                INSERT IGNORE INTO presenca (
                    id_aula,
                    id_aluno,
                    status,
                    origem
                )
                VALUES (
                    %s,
                    %s,
                    'Pendente',
                    'Sistema'
                )
            """, (
                id_aula,
                aluno['id_aluno']
            ))

            presencas_criadas += cursor.rowcount

        conexao.commit()

        return jsonify({
            'mensagem': 'Chamada gerada com sucesso.',
            'id_aula': id_aula,
            'alunos_encontrados': len(alunos),
            'presencas_criadas': presencas_criadas
        })

    except Error as erro:
        conexao.rollback()

        return resposta_erro(
            f'Erro ao gerar chamada: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@chamadas_bp.post('/api/chamadas/<int:id_aula>/processar')
def processar_chamada(id_aula):
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

        aula, erro = validar_aula_e_acesso(
            cursor,
            id_aula
        )

        if erro:
            conexao.rollback()
            return erro

        if aula['status'] == 'Cancelada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível processar chamada de uma aula cancelada.'
            )

        if aula['status'] == 'Finalizada':
            conexao.rollback()

            return resposta_erro(
                'A chamada de uma aula finalizada '
                'não pode ser processada novamente.'
            )

        if aula['status'] != 'Em andamento':
            conexao.rollback()

            return resposta_erro(
                'A aula precisa estar em andamento '
                'para processar registros RFID.'
            )

        cursor.execute("""
            SELECT
                TIMESTAMP(
                    data_aula,
                    horario_inicio
                ) AS inicio_aula,

                DATE_SUB(
                    TIMESTAMP(
                        data_aula,
                        horario_inicio
                    ),
                    INTERVAL %s MINUTE
                ) AS inicio_janela,

                DATE_ADD(
                    TIMESTAMP(
                        data_aula,
                        horario_inicio
                    ),
                    INTERVAL tolerancia_minutos MINUTE
                ) AS limite_presenca,

                TIMESTAMP(
                    data_aula,
                    horario_fim
                ) AS fim_aula
            FROM aula
            WHERE id_aula = %s
        """, (
            ANTECEDENCIA_MINUTOS,
            id_aula
        ))

        janela = cursor.fetchone()

        cursor.execute("""
            SELECT
                pr.id_presenca,
                pr.id_aluno,
                al.status AS status_aluno
            FROM presenca pr
            INNER JOIN aluno al
                ON al.id_aluno = pr.id_aluno
            WHERE pr.id_aula = %s
              AND pr.status = 'Pendente'
            ORDER BY pr.id_aluno
        """, (id_aula,))

        presencas = cursor.fetchall()

        if not presencas:
            conexao.commit()

            return jsonify({
                'mensagem': 'Não há presenças pendentes para processar.',
                'id_aula': id_aula,
                'processadas': 0,
                'presentes': 0,
                'atrasados': 0,
                'sem_leitura': 0
            })

        presentes = 0
        atrasados = 0
        sem_leitura = 0

        for presenca in presencas:
            if presenca['status_aluno'] != 'Ativo':
                sem_leitura += 1
                continue

            cursor.execute("""
                SELECT
                    r.id_registro,
                    r.data_hora,
                    r.tipo
                FROM registro_rfid r
                WHERE r.id_aluno = %s
                  AND r.id_ambiente = %s
                  AND r.tipo IN (
                      'Entrada',
                      'Movimentação'
                  )
                  AND r.data_hora >= %s
                  AND r.data_hora <= %s
                ORDER BY r.data_hora ASC
                LIMIT 1
            """, (
                presenca['id_aluno'],
                aula['id_ambiente'],
                janela['inicio_janela'],
                janela['fim_aula']
            ))

            registro = cursor.fetchone()

            if registro is None:
                sem_leitura += 1
                continue

            if (
                registro['data_hora']
                <= janela['limite_presenca']
            ):
                novo_status = 'Presente'
                presentes += 1

            else:
                novo_status = 'Atrasado'
                atrasados += 1

            cursor.execute("""
                UPDATE presenca
                SET
                    id_registro_rfid = %s,
                    status = %s,
                    origem = 'RFID',
                    horario_detectado = %s,
                    observacao = %s,
                    atualizado_em = NOW()
                WHERE id_presenca = %s
            """, (
                registro['id_registro'],
                novo_status,
                registro['data_hora'],
                (
                    'Presença identificada automaticamente '
                    'por registro RFID.'
                ),
                presenca['id_presenca']
            ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Chamada processada com sucesso.',
            'id_aula': id_aula,
            'processadas': presentes + atrasados,
            'presentes': presentes,
            'atrasados': atrasados,
            'sem_leitura': sem_leitura
        })

    except Error as erro:
        conexao.rollback()

        return resposta_erro(
            f'Erro ao processar chamada: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@chamadas_bp.post('/api/chamadas/<int:id_aula>/finalizar')
def finalizar_chamada(id_aula):
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

        aula, erro = validar_aula_e_acesso(
            cursor,
            id_aula
        )

        if erro:
            conexao.rollback()
            return erro

        if aula['status'] == 'Cancelada':
            conexao.rollback()

            return resposta_erro(
                'Não é possível finalizar a chamada '
                'de uma aula cancelada.'
            )

        if aula['status'] == 'Finalizada':
            conexao.rollback()

            return resposta_erro(
                'A chamada desta aula já foi finalizada.'
            )

        if aula['status'] != 'Em andamento':
            conexao.rollback()

            return resposta_erro(
                'A aula precisa estar em andamento '
                'para finalizar a chamada.'
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
                'A chamada ainda não foi gerada para esta aula.'
            )

        cursor.execute("""
            UPDATE presenca
            SET
                status = 'Ausente',
                origem = 'Sistema',
                observacao = (
                    'Ausência definida automaticamente '
                    'no encerramento da aula.'
                ),
                atualizado_em = NOW()
            WHERE id_aula = %s
              AND status = 'Pendente'
        """, (id_aula,))

        ausencias_geradas = cursor.rowcount

        cursor.execute("""
            UPDATE aula
            SET
                status = 'Finalizada',
                atualizado_em = NOW()
            WHERE id_aula = %s
        """, (id_aula,))

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM presenca
            WHERE id_aula = %s
            GROUP BY status
        """, (id_aula,))

        registros_resumo = cursor.fetchall()

        resumo = {
            'Pendente': 0,
            'Presente': 0,
            'Atrasado': 0,
            'Ausente': 0,
            'Justificado': 0
        }

        for item in registros_resumo:
            resumo[item['status']] = item['total']

        conexao.commit()

        return jsonify({
            'mensagem': 'Chamada finalizada com sucesso.',
            'id_aula': id_aula,
            'ausencias_geradas': ausencias_geradas,
            'resumo': resumo
        })

    except Error as erro:
        conexao.rollback()

        return resposta_erro(
            f'Erro ao finalizar chamada: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()
