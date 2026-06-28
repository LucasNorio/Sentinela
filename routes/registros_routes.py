from flask import Blueprint, jsonify, request
from mysql.connector import Error
from database import obter_conexao

registros_bp = Blueprint('registros', __name__)

TIPOS_REGISTRO_VALIDOS = {
    'Entrada',
    'Saída',
    'Movimentação',
    'Alerta'
}


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def normalizar_codigo(valor):
    return str(valor or '').strip().upper()


def validar_dados_registro(dados):
    codigo_tag_lida = normalizar_codigo(
        dados.get('codigo_tag_lida') or dados.get('codigo_tag') or dados.get('tag')
    )

    codigo_leitor = normalizar_codigo(
        dados.get('codigo_leitor') or dados.get('codigo_identificacao') or dados.get('leitor')
    )

    tipo = dados.get('tipo', 'Movimentação')
    observacao = str(dados.get('observacao', '')).strip()

    if not codigo_tag_lida:
        return None, 'O código da tag é obrigatório.'

    if not codigo_leitor:
        return None, 'O código do leitor é obrigatório.'

    if tipo not in TIPOS_REGISTRO_VALIDOS:
        return None, 'Tipo de registro inválido.'

    return {
        'codigo_tag_lida': codigo_tag_lida,
        'codigo_leitor': codigo_leitor,
        'tipo': tipo,
        'observacao': observacao
    }, None


@registros_bp.get('/api/registros-rfid')
def listar_registros_rfid():
    tipo = request.args.get('tipo', 'Todos')
    limite = request.args.get('limite', 100)

    if tipo != 'Todos' and tipo not in TIPOS_REGISTRO_VALIDOS:
        return resposta_erro('Tipo de registro inválido.')

    try:
        limite = int(limite)
    except (ValueError, TypeError):
        return resposta_erro('Limite inválido.')

    if limite < 1:
        limite = 1

    if limite > 500:
        limite = 500

    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        consulta = """
            SELECT
                r.id_registro AS id,
                r.codigo_tag_lida,
                r.id_tag,
                r.id_aluno,
                r.id_leitor,
                r.id_ambiente,
                r.tipo,
                CAST(r.data_hora AS CHAR) AS data_hora,
                r.observacao,

                t.codigo AS codigo_tag_cadastrada,
                t.status AS status_tag,

                al.nome AS aluno,
                al.status AS status_aluno,

                l.nome AS leitor,
                l.codigo_identificacao AS codigo_leitor,
                l.tipo_leitor,
                l.status AS status_leitor,

                a.nome AS ambiente,
                a.bloco,
                a.tipo AS tipo_ambiente,
                a.status AS status_ambiente
            FROM registro_rfid r
            LEFT JOIN tag_rfid t ON t.id_tag = r.id_tag
            LEFT JOIN aluno al ON al.id_aluno = r.id_aluno
            INNER JOIN leitor_rfid l ON l.id_leitor = r.id_leitor
            INNER JOIN ambiente a ON a.id_ambiente = r.id_ambiente
        """

        parametros = []

        if tipo != 'Todos':
            consulta += " WHERE r.tipo = %s"
            parametros.append(tipo)

        consulta += " ORDER BY r.data_hora DESC LIMIT %s"
        parametros.append(limite)

        cursor.execute(consulta, tuple(parametros))

        return jsonify(cursor.fetchall())

    except Error as erro:
        return resposta_erro(f'Erro ao listar registros RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()


@registros_bp.post('/api/registros-rfid')
def cadastrar_registro_rfid():
    dados = request.get_json(silent=True) or {}
    registro, erro_validacao = validar_dados_registro(dados)

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
            SELECT
                l.id_leitor,
                l.id_ambiente,
                l.status AS status_leitor,
                a.status AS status_ambiente
            FROM leitor_rfid l
            INNER JOIN ambiente a ON a.id_ambiente = l.id_ambiente
            WHERE l.codigo_identificacao = %s
        """, (registro['codigo_leitor'],))

        leitor = cursor.fetchone()

        if leitor is None:
            conexao.rollback()
            return resposta_erro('Leitor RFID não encontrado.', 404)

        cursor.execute("""
            SELECT
                t.id_tag,
                t.id_aluno,
                t.status AS status_tag,
                al.status AS status_aluno
            FROM tag_rfid t
            LEFT JOIN aluno al ON al.id_aluno = t.id_aluno
            WHERE t.codigo = %s
        """, (registro['codigo_tag_lida'],))

        tag = cursor.fetchone()

        tipo_registro = registro['tipo']
        observacao = registro['observacao']
        id_tag = None
        id_aluno = None

        if leitor['status_leitor'] != 'Ativo':
            tipo_registro = 'Alerta'
            observacao = f"Leitura recebida de leitor com status {leitor['status_leitor']}."

        elif leitor['status_ambiente'] != 'Ativo':
            tipo_registro = 'Alerta'
            observacao = f"Leitura recebida em ambiente com status {leitor['status_ambiente']}."

        elif tag is None:
            tipo_registro = 'Alerta'
            observacao = 'Tag RFID não cadastrada no sistema.'

        else:
            id_tag = tag['id_tag']
            id_aluno = tag['id_aluno']

            if tag['status_tag'] != 'Ativa':
                tipo_registro = 'Alerta'
                observacao = f"Tag RFID com status {tag['status_tag']}."

            elif tag['status_aluno'] != 'Ativo':
                tipo_registro = 'Alerta'
                observacao = f"Aluno vinculado à tag está com status {tag['status_aluno']}."

        observacao = observacao[:255] if observacao else None

        cursor.execute("""
            INSERT INTO registro_rfid
                (
                    codigo_tag_lida,
                    id_tag,
                    id_aluno,
                    id_leitor,
                    id_ambiente,
                    tipo,
                    observacao
                )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
        """, (
            registro['codigo_tag_lida'],
            id_tag,
            id_aluno,
            leitor['id_leitor'],
            leitor['id_ambiente'],
            tipo_registro,
            observacao
        ))

        id_registro = cursor.lastrowid

        cursor.execute("""
            UPDATE leitor_rfid
            SET ultima_comunicacao = NOW()
            WHERE id_leitor = %s
        """, (leitor['id_leitor'],))

        conexao.commit()

        return jsonify({
            'mensagem': 'Registro RFID cadastrado com sucesso.',
            'id_registro': id_registro,
            'tipo': tipo_registro,
            'alerta': tipo_registro == 'Alerta'
        }), 201

    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar registro RFID: {erro}', 500)

    finally:
        if cursor:
            cursor.close()

        conexao.close()