from flask import Blueprint, jsonify
from mysql.connector import Error
from database import obter_conexao

dashboard_bp = Blueprint('dashboard', __name__)


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def consultar_contagem(cursor, sql, parametros=None):
    cursor.execute(sql, parametros or ())
    resultado = cursor.fetchone()
    return resultado['total'] if resultado else 0


@dashboard_bp.get('/api/dashboard/resumo')
def resumo_dashboard():
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        alunos_ativos = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM aluno
            WHERE status = 'Ativo'
        """)

        alunos_cadastrados = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM aluno
        """)

        professores_ativos = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM professor
            WHERE status = 'Ativo'
        """)

        turmas_ativas = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM turma
            WHERE status = 'Ativa'
        """)

        ambientes_ativos = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM ambiente
            WHERE status = 'Ativo'
        """)

        leitores_ativos = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM leitor_rfid
            WHERE status = 'Ativo'
        """)

        leitores_manutencao = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM leitor_rfid
            WHERE status = 'Manutenção'
        """)

        registros_hoje = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM registro_rfid
            WHERE DATE(data_hora) = CURDATE()
        """)

        alertas_hoje = consultar_contagem(cursor, """
            SELECT COUNT(*) AS total
            FROM registro_rfid
            WHERE tipo = 'Alerta'
            AND DATE(data_hora) = CURDATE()
        """)

        cursor.execute("""
            SELECT
                r.id_registro AS id,
                r.codigo_tag_lida,
                r.tipo,
                CAST(r.data_hora AS CHAR) AS data_hora,
                r.observacao,

                al.nome AS aluno,

                l.nome AS leitor,
                l.codigo_identificacao AS codigo_leitor,

                a.nome AS ambiente,
                a.bloco
            FROM registro_rfid r
            LEFT JOIN aluno al ON al.id_aluno = r.id_aluno
            INNER JOIN leitor_rfid l ON l.id_leitor = r.id_leitor
            INNER JOIN ambiente a ON a.id_ambiente = r.id_ambiente
            ORDER BY r.data_hora DESC
            LIMIT 5
        """)

        ultimos_registros = cursor.fetchall()

        return jsonify({
            'alunos_ativos': alunos_ativos,
            'alunos_cadastrados': alunos_cadastrados,
            'professores_ativos': professores_ativos,
            'turmas_ativas': turmas_ativas,
            'ambientes_ativos': ambientes_ativos,
            'leitores_ativos': leitores_ativos,
            'leitores_manutencao': leitores_manutencao,
            'registros_hoje': registros_hoje,
            'alertas_hoje': alertas_hoje,
            'ultimos_registros': ultimos_registros
        })

    except Error as erro:
        return resposta_erro(f'Erro ao carregar resumo do dashboard: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()