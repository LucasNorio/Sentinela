from flask import Blueprint, jsonify, request, session
from mysql.connector import Error

from database import obter_conexao


presencas_bp = Blueprint('presencas', __name__)


STATUS_CORRECAO_VALIDOS = {
    'Presente',
    'Atrasado',
    'Ausente',
    'Justificado'
}


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def formatar_data_hora(valor):
    if valor is None:
        return None

    return valor.strftime('%Y-%m-%d %H:%M:%S')


def buscar_usuario_atual(cursor):
    usuario_sessao = session.get('usuario')

    if not usuario_sessao:
        return None

    cursor.execute("""
        SELECT
            id_usuario,
            nome,
            email,
            perfil,
            status,
            id_professor
        FROM usuario
        WHERE id_usuario = %s
    """, (
        usuario_sessao['id'],
    ))

    return cursor.fetchone()


def buscar_contexto_presenca(
    cursor,
    id_presenca
):
    cursor.execute("""
        SELECT
            pr.id_presenca,
            pr.id_aula,
            pr.id_aluno,
            pr.status AS status_presenca,
            pr.origem,
            pr.id_registro_rfid,
            pr.horario_detectado,
            al.nome AS aluno,
            al.matricula,
            a.id_professor,
            a.status AS status_aula,
            a.data_aula,
            a.horario_inicio,
            a.horario_fim,
            t.id_turma,
            t.nome AS turma,
            p.nome AS professor
        FROM presenca pr
        INNER JOIN aluno al
            ON al.id_aluno = pr.id_aluno
        INNER JOIN aula a
            ON a.id_aula = pr.id_aula
        INNER JOIN turma t
            ON t.id_turma = a.id_turma
        INNER JOIN professor p
            ON p.id_professor = a.id_professor
        WHERE pr.id_presenca = %s
    """, (
        id_presenca,
    ))

    return cursor.fetchone()


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


def pode_visualizar_presenca(
    cursor,
    usuario,
    presenca
):
    if usuario['perfil'] in {
        'Administrador',
        'Coordenação',
        'Secretaria'
    }:
        return True

    if usuario['perfil'] == 'Professor':
        return professor_tem_acesso_turma(
            cursor,
            usuario['id_professor'],
            presenca['id_turma']
        )

    return False


def pode_corrigir_presenca(
    cursor,
    usuario,
    presenca
):
    if usuario['perfil'] in {
        'Administrador',
        'Coordenação'
    }:
        return True

    if usuario['perfil'] == 'Professor':
        return professor_tem_acesso_turma(
            cursor,
            usuario['id_professor'],
            presenca['id_turma']
        )

    return False


def validar_usuario_ativo(usuario):
    if usuario is None:
        return resposta_erro(
            'Usuário não autenticado.',
            401
        )

    if usuario['status'] != 'Ativo':
        return resposta_erro(
            'Usuário inativo.',
            403
        )

    return None


def validar_estado_correcao(presenca):
    if presenca['status_aula'] == 'Cancelada':
        return resposta_erro(
            'Não é possível corrigir presença de uma aula cancelada.'
        )

    if presenca['status_aula'] == 'Programada':
        return resposta_erro(
            'A aula precisa estar em andamento ou finalizada '
            'para permitir correções de presença.'
        )

    if presenca['status_aula'] not in {
        'Em andamento',
        'Finalizada'
    }:
        return resposta_erro(
            'A aula não está em um estado válido '
            'para correção de presença.'
        )

    return None


@presencas_bp.patch(
    '/api/presencas/<int:id_presenca>/corrigir'
)
def corrigir_presenca(id_presenca):
    dados = request.get_json(
        silent=True
    ) or {}

    status_novo = str(
        dados.get('status', '')
    ).strip()

    motivo = str(
        dados.get('motivo', '')
    ).strip()

    if not status_novo:
        return resposta_erro(
            'O novo status é obrigatório.'
        )

    if status_novo not in STATUS_CORRECAO_VALIDOS:
        return resposta_erro(
            'Status de presença inválido.'
        )

    if not motivo:
        return resposta_erro(
            'O motivo da correção é obrigatório.'
        )

    if len(motivo) > 255:
        return resposta_erro(
            'O motivo da correção deve possuir '
            'no máximo 255 caracteres.'
        )

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(
            dictionary=True
        )

        conexao.start_transaction()

        usuario = buscar_usuario_atual(
            cursor
        )

        erro_usuario = validar_usuario_ativo(
            usuario
        )

        if erro_usuario:
            conexao.rollback()
            return erro_usuario

        presenca = buscar_contexto_presenca(
            cursor,
            id_presenca
        )

        if presenca is None:
            conexao.rollback()

            return resposta_erro(
                'Presença não encontrada.',
                404
            )

        erro_estado = validar_estado_correcao(
            presenca
        )

        if erro_estado:
            conexao.rollback()
            return erro_estado

        if not pode_corrigir_presenca(
            cursor,
            usuario,
            presenca
        ):
            conexao.rollback()

            if (
                usuario['perfil'] == 'Professor'
                and usuario['id_professor'] is None
            ):
                return resposta_erro(
                    'Este usuário Professor ainda não está vinculado '
                    'a um cadastro de professor.',
                    403
                )

            return resposta_erro(
                'Usuário sem permissão para corrigir esta presença.',
                403
            )

        status_anterior = presenca[
            'status_presenca'
        ]

        if status_anterior == status_novo:
            conexao.rollback()

            return resposta_erro(
                (
                    'A presença já está com status '
                    f'{status_novo}.'
                ),
                409
            )

        cursor.execute("""
            INSERT INTO ajuste_presenca (
                id_presenca,
                id_usuario,
                status_anterior,
                status_novo,
                motivo
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            id_presenca,
            usuario['id_usuario'],
            status_anterior,
            status_novo,
            motivo
        ))

        id_ajuste = cursor.lastrowid

        cursor.execute("""
            UPDATE presenca
            SET
                status = %s,
                origem = 'Correção',
                observacao = %s,
                atualizado_em = NOW()
            WHERE id_presenca = %s
        """, (
            status_novo,
            f'Correção manual: {motivo}',
            id_presenca
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Presença corrigida com sucesso.',
            'id_presenca': id_presenca,
            'id_ajuste': id_ajuste,
            'aluno': presenca['aluno'],
            'status_anterior': status_anterior,
            'status_novo': status_novo,
            'motivo': motivo,
            'usuario': usuario['nome']
        })

    except Error as erro:
        conexao.rollback()

        return resposta_erro(
            f'Erro ao corrigir presença: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@presencas_bp.get(
    '/api/presencas/<int:id_presenca>/ajustes'
)
def listar_ajustes_presenca(id_presenca):
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro(
            'Não foi possível conectar ao banco de dados.',
            500
        )

    cursor = None

    try:
        cursor = conexao.cursor(
            dictionary=True
        )

        usuario = buscar_usuario_atual(
            cursor
        )

        erro_usuario = validar_usuario_ativo(
            usuario
        )

        if erro_usuario:
            return erro_usuario

        presenca = buscar_contexto_presenca(
            cursor,
            id_presenca
        )

        if presenca is None:
            return resposta_erro(
                'Presença não encontrada.',
                404
            )

        if not pode_visualizar_presenca(
            cursor,
            usuario,
            presenca
        ):
            if (
                usuario['perfil'] == 'Professor'
                and usuario['id_professor'] is None
            ):
                return resposta_erro(
                    'Este usuário Professor ainda não está vinculado '
                    'a um cadastro de professor.',
                    403
                )

            return resposta_erro(
                'Usuário sem permissão para visualizar '
                'os ajustes desta presença.',
                403
            )

        cursor.execute("""
            SELECT
                ap.id_ajuste_presenca AS id,
                ap.id_presenca,
                ap.status_anterior,
                ap.status_novo,
                ap.motivo,
                ap.criado_em,
                u.id_usuario,
                u.nome AS usuario,
                u.perfil AS perfil_usuario
            FROM ajuste_presenca ap
            INNER JOIN usuario u
                ON u.id_usuario = ap.id_usuario
            WHERE ap.id_presenca = %s
            ORDER BY
                ap.criado_em DESC,
                ap.id_ajuste_presenca DESC
        """, (
            id_presenca,
        ))

        ajustes = cursor.fetchall()

        return jsonify({
            'presenca': {
                'id': presenca['id_presenca'],
                'aluno': presenca['aluno'],
                'matricula': presenca['matricula'],
                'turma': presenca['turma'],
                'professor': presenca['professor'],
                'status_atual': presenca['status_presenca'],
                'origem': presenca['origem']
            },
            'ajustes': [
                {
                    'id': ajuste['id'],
                    'status_anterior': ajuste['status_anterior'],
                    'status_novo': ajuste['status_novo'],
                    'motivo': ajuste['motivo'],
                    'usuario': ajuste['usuario'],
                    'perfil_usuario': ajuste['perfil_usuario'],
                    'criado_em': formatar_data_hora(
                        ajuste['criado_em']
                    )
                }
                for ajuste in ajustes
            ],
            'total': len(ajustes)
        })

    except Error as erro:
        return resposta_erro(
            f'Erro ao listar ajustes de presença: {erro}',
            500
        )

    finally:
        if cursor:
            cursor.close()

        conexao.close()
