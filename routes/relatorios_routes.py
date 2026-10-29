from datetime import date, datetime
from io import BytesIO
import re
from xml.sax.saxutils import escape

from flask import Blueprint, jsonify, request, send_file, session
from mysql.connector import Error

from database import obter_conexao

relatorios_bp = Blueprint('relatorios', __name__)

PERFIS_RELATORIOS = {'Administrador', 'Coordenação', 'Secretaria', 'Professor'}


def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status


def validar_periodo():
    inicio_texto = (request.args.get('inicio') or '').strip()
    fim_texto = (request.args.get('fim') or '').strip()

    if not (re.fullmatch(r'\d{4}-\d{2}-\d{2}', inicio_texto)
            and re.fullmatch(r'\d{4}-\d{2}-\d{2}', fim_texto)):
        raise ValueError('Informe as datas inicial e final no formato AAAA-MM-DD.')

    try:
        inicio = date.fromisoformat(inicio_texto)
        fim = date.fromisoformat(fim_texto)
    except ValueError:
        raise ValueError('Informe as datas inicial e final no formato AAAA-MM-DD.')

    if inicio > fim:
        raise ValueError('A data inicial não pode ser posterior à data final.')

    if (fim - inicio).days > 366:
        raise ValueError('O período máximo permitido é de 367 dias corridos.')

    return inicio, fim


def validar_usuario(cursor):
    usuario_sessao = session.get('usuario') or {}
    if not usuario_sessao.get('id'):
        raise PermissionError('Usuário não autenticado.')

    cursor.execute('''
        SELECT id_usuario, id_professor, perfil, status
        FROM usuario
        WHERE id_usuario = %s
    ''', (usuario_sessao['id'],))
    usuario = cursor.fetchone()

    if not usuario or usuario['status'] != 'Ativo' or usuario['perfil'] not in PERFIS_RELATORIOS:
        raise PermissionError('Usuário não possui acesso aos relatórios.')

    return usuario


def filtrar_acesso_turma(cursor, usuario, id_turma):
    if usuario['perfil'] != 'Professor':
        return

    if not usuario['id_professor']:
        raise PermissionError('Professor sem cadastro vinculado ao usuário.')

    cursor.execute('''
        SELECT 1 AS permitido
        FROM professor_turma
        WHERE id_professor = %s
          AND id_turma = %s
          AND status = 'Ativo'
          AND funcao IN ('Professor', 'Auxiliar')
        LIMIT 1
    ''', (usuario['id_professor'], id_turma))

    if cursor.fetchone() is None:
        raise PermissionError('Você não possui acesso aos relatórios desta turma.')


def listar_turmas_permitidas(cursor, usuario):
    if usuario['perfil'] == 'Professor':
        if not usuario['id_professor']:
            return []

        cursor.execute('''
            SELECT t.id_turma AS id, t.nome, t.ano_letivo, t.periodo,
                   t.status, c.nome AS curso
            FROM turma t
            INNER JOIN curso c ON c.id_curso = t.id_curso
            WHERE EXISTS (
                SELECT 1 FROM professor_turma pt
                WHERE pt.id_turma = t.id_turma
                  AND pt.id_professor = %s
                  AND pt.status = 'Ativo'
                  AND pt.funcao IN ('Professor', 'Auxiliar')
            )
            ORDER BY t.ano_letivo DESC, c.nome, t.nome
        ''', (usuario['id_professor'],))
    else:
        cursor.execute('''
            SELECT t.id_turma AS id, t.nome, t.ano_letivo, t.periodo,
                   t.status, c.nome AS curso
            FROM turma t
            INNER JOIN curso c ON c.id_curso = t.id_curso
            ORDER BY t.ano_letivo DESC, c.nome, t.nome
        ''')

    return cursor.fetchall()


def consultar_relatorio(cursor, id_turma, inicio, fim):
    cursor.execute('''
        SELECT t.id_turma, t.nome AS turma, t.periodo, t.ano_letivo,
               t.semestre, t.status AS status_turma, c.nome AS curso
        FROM turma t
        INNER JOIN curso c ON c.id_curso = t.id_curso
        WHERE t.id_turma = %s
    ''', (id_turma,))
    turma = cursor.fetchone()

    if turma is None:
        raise LookupError('Turma não encontrada.')

    cursor.execute('''
        SELECT COUNT(*) AS total
        FROM aula a
        WHERE a.id_turma = %s
          AND a.data_aula BETWEEN %s AND %s
          AND a.status = 'Finalizada'
    ''', (id_turma, inicio, fim))
    aulas_finalizadas = cursor.fetchone()['total']

    if not aulas_finalizadas:
        raise ValueError('Não existem aulas finalizadas nessa turma e nesse período.')

    cursor.execute('''
        SELECT COUNT(*) AS total
        FROM presenca p
        INNER JOIN aula a ON a.id_aula = p.id_aula
        WHERE a.id_turma = %s
          AND a.data_aula BETWEEN %s AND %s
          AND a.status = 'Finalizada'
          AND p.status = 'Pendente'
    ''', (id_turma, inicio, fim))
    pendencias = cursor.fetchone()['total']

    if pendencias:
        raise RuntimeError(
            f'Existem {pendencias} presenças pendentes em aulas finalizadas. '
            'Regularize os registros antes de emitir o relatório.'
        )

    cursor.execute('''
        SELECT al.id_aluno AS id, al.nome, al.matricula,
               al.status AS status_aluno,
               COUNT(*) AS aulas_com_registro,
               SUM(CASE WHEN p.status = 'Presente' THEN 1 ELSE 0 END) AS presentes,
               SUM(CASE WHEN p.status = 'Atrasado' THEN 1 ELSE 0 END) AS atrasados,
               SUM(CASE WHEN p.status = 'Ausente' THEN 1 ELSE 0 END) AS ausentes,
               SUM(CASE WHEN p.status = 'Justificado' THEN 1 ELSE 0 END) AS justificados
        FROM presenca p
        INNER JOIN aula a ON a.id_aula = p.id_aula
        INNER JOIN aluno al ON al.id_aluno = p.id_aluno
        WHERE a.id_turma = %s
          AND a.data_aula BETWEEN %s AND %s
          AND a.status = 'Finalizada'
        GROUP BY al.id_aluno, al.nome, al.matricula, al.status
        ORDER BY al.nome, al.id_aluno
    ''', (id_turma, inicio, fim))
    presencas = cursor.fetchall()

    # A turma atual não permite reconstruir transferências históricas.
    # Incluímos alunos atualmente nela e alunos com registros nas aulas consultadas.
    cursor.execute('''
        SELECT id_aluno AS id, nome, matricula, status AS status_aluno
        FROM aluno
        WHERE id_turma = %s
        ORDER BY nome, id_aluno
    ''', (id_turma,))
    alunos_atuais = cursor.fetchall()

    consolidado = {aluno['id']: dict(aluno) for aluno in alunos_atuais}

    for presenca in presencas:
        consolidado[presenca['id']] = dict(presenca)

    alunos = []
    cobertura_parcial = 0

    for aluno in sorted(consolidado.values(), key=lambda a: (a['nome'].casefold(), a['id'])):
        registros = int(aluno.get('aulas_com_registro') or 0)
        presentes = int(aluno.get('presentes') or 0)
        atrasados = int(aluno.get('atrasados') or 0)
        ausentes = int(aluno.get('ausentes') or 0)
        justificados = int(aluno.get('justificados') or 0)

        # Sem histórico de matrícula/transferência, não podemos atribuir faltas
        # automaticamente aos dias sem registro, nem certificar um percentual
        # baseado apenas nas aulas em que o aluno possui presença cadastrada.
        if registros > aulas_finalizadas:
            raise RuntimeError(
                'Quantidade de presenças maior que a de aulas finalizadas. '
                'Verifique a integridade dos registros antes de emitir o relatório.'
            )

        parcial = registros < aulas_finalizadas
        cobertura_parcial += int(parcial)

        alunos.append({
            'id': aluno['id'],
            'nome': aluno['nome'],
            'matricula': aluno['matricula'],
            'status_aluno': aluno['status_aluno'],
            'aulas_com_registro': registros,
            'registros_faltantes': aulas_finalizadas - registros,
            'presentes': presentes,
            'atrasados': atrasados,
            'ausentes': ausentes,
            'justificados': justificados,
            'frequencia_percentual': (
                round(100 * (presentes + atrasados) / registros, 2)
                if registros and not parcial else None
            ),
            'cobertura_parcial': parcial,
        })

    return {
        'turma': turma,
        'periodo': {'inicio': inicio.isoformat(), 'fim': fim.isoformat()},
        'aulas_finalizadas': aulas_finalizadas,
        'alunos': alunos,
        'total_alunos': len(alunos),
        'alunos_cobertura_completa': len(alunos) - cobertura_parcial,
        'alunos_cobertura_parcial': cobertura_parcial,
        'criterios': {
            'aulas': 'Somente aulas finalizadas.',
            'presencas': 'Dados consolidados da tabela presenca, incluindo correções posteriores.',
            'frequencia': '(Presentes + Atrasados) / aulas com registro * 100, somente com cobertura completa.',
            'justificadas': 'Justificado integra o denominador, mas não conta como comparecimento.',
            'cobertura_parcial': (
                'Se existem menos registros que aulas finalizadas, o percentual fica '
                'indisponível até a conferência acadêmica. O sistema não deduz faltas '
                'nem presume a data de ingresso ou transferência do aluno.'
            ),
        },
    }


def criar_pdf(dados):
    """Emite documento A4 horizontal; não atesta frequências incompletas."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        LongTable, Paragraph, SimpleDocTemplate,
        Spacer, Table, TableStyle,
    )

    vinho = colors.HexColor('#AA2635')
    azul = colors.HexColor('#233047')
    cinza = colors.HexColor('#667085')
    borda = colors.HexColor('#E5E9EF')
    superficie = colors.HexColor('#F5F7FA')
    alerta_fundo = colors.HexColor('#FFF4DF')
    alerta_texto = colors.HexColor('#855514')
    branco = colors.white

    buffer = BytesIO()
    largura_pagina, altura_pagina = landscape(A4)
    documento = SimpleDocTemplate(
        buffer,
        pagesize=(largura_pagina, altura_pagina),
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=30 * mm, bottomMargin=21 * mm,
        title='Sentinela | Frequência por turma',
        author='Sistema Sentinela',
        subject='Relatório de presença escolar consolidada',
    )
    largura = documento.width
    padrao = getSampleStyleSheet()

    titulo = ParagraphStyle(
        'RelTituloV05', parent=padrao['Heading1'],
        fontName='Helvetica-Bold', fontSize=17.5, leading=23,
        textColor=azul, spaceAfter=2 * mm,
    )
    subtitulo = ParagraphStyle(
        'RelSubtituloV05', parent=padrao['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=13.5,
        textColor=cinza,
    )
    metadado = ParagraphStyle(
        'RelMetaV05', parent=padrao['Normal'],
        fontName='Helvetica', fontSize=9, leading=13,
        textColor=azul,
    )
    indicador = ParagraphStyle(
        'RelIndicadorV05', parent=padrao['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=18,
        textColor=azul,
    )
    rotulo = ParagraphStyle(
        'RelRotuloV05', parent=padrao['Normal'],
        fontName='Helvetica', fontSize=8, leading=10,
        textColor=cinza,
    )
    celula = ParagraphStyle(
        'RelCelulaV05', parent=padrao['Normal'],
        fontName='Helvetica', fontSize=8.2, leading=11,
        textColor=azul,
    )
    central = ParagraphStyle('RelCentralV05', parent=celula, alignment=TA_CENTER)
    direita = ParagraphStyle('RelDireitaV05', parent=celula, alignment=TA_RIGHT)
    cabecalho = ParagraphStyle(
        'RelCabV05', parent=central,
        fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=branco,
    )
    nota = ParagraphStyle(
        'RelNotaV05', parent=padrao['Normal'],
        fontName='Helvetica', fontSize=7.7, leading=10.4,
        textColor=cinza,
    )
    alerta = ParagraphStyle(
        'RelAlertaV05', parent=nota,
        fontName='Helvetica-Bold', textColor=alerta_texto,
    )

    def pvalor(valor, estilo=celula):
        return Paragraph(escape(str(valor if valor is not None else '-')), estilo)

    def data_br(iso):
        return date.fromisoformat(iso).strftime('%d/%m/%Y')

    def campo(nome, valor):
        return Paragraph(
            f'<font color="#667085" size="8">{escape(nome.upper())}</font>'
            f'<br/><b>{escape(str(valor))}</b>', metadado
        )

    conteudo = [
        Paragraph('Relatório de frequência por turma', titulo),
        Paragraph('Consolidação de presenças nas aulas finalizadas do período.', subtitulo),
        Spacer(1, 2.5 * mm),
    ]
    turma = dados['turma']
    meta = Table([
        [campo('Curso', turma['curso']), campo('Turma', turma['turma'])],
        [campo('Período consultado', f"{data_br(dados['periodo']['inicio'])} a {data_br(dados['periodo']['fim'])}"),
         campo('Ano letivo / turno', f"{turma['ano_letivo']} / {turma['periodo']}")],
    ], colWidths=[largura * .55, largura * .45], hAlign='LEFT')
    meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), superficie),
        ('BOX', (0, 0), (-1, -1), .45, borda),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 13),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    conteudo.extend([meta, Spacer(1, 2.5 * mm)])

    estatisticas = [
        ('AULAS FINALIZADAS', dados['aulas_finalizadas']),
        ('ALUNOS LISTADOS', dados['total_alunos']),
        ('COBERTURA COMPLETA', dados['alunos_cobertura_completa']),
        ('A CONFERIR', dados['alunos_cobertura_parcial']),
    ]
    cards = Table([[
        [Paragraph(rot, rotulo), Spacer(1, 2 * mm), Paragraph(str(valor), indicador)]
        for rot, valor in estatisticas
    ]], colWidths=[largura / 4] * 4, hAlign='LEFT')
    cards.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), branco),
        ('BOX', (0, 0), (-1, -1), .5, borda),
        ('INNERGRID', (0, 0), (-1, -1), .4, borda),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    conteudo.extend([cards, Spacer(1, 2.5 * mm)])

    incompletos = dados['alunos_cobertura_parcial'] > 0
    if incompletos:
        caixa = Table([[
            Paragraph(
                '<b>CONFERÊNCIA NECESSÁRIA</b>  |  '
                'Há alunos com registros incompletos: frequência N/D. '
                'Verifique as matrículas e os lançamentos antes de utilizar '
                'o relatório como comprovante oficial.', alerta
            )
        ]], colWidths=[largura])
        caixa.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), alerta_fundo),
            ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor('#D99627')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 11),
        ]))
        conteudo.extend([caixa, Spacer(1, 2.5 * mm)])

    headers = ['Matrícula', 'Aluno', 'P', 'A', 'F', 'J', 'Cobertura', 'Frequência', 'Situação']
    linhas = [[Paragraph(escape(t), cabecalho) for t in headers]]

    for aluno in dados['alunos']:
        cobertura = f"{aluno['aulas_com_registro']}/{dados['aulas_finalizadas']}"
        percentual = ('N/D' if aluno['frequencia_percentual'] is None
                      else f"{aluno['frequencia_percentual']:.2f}%".replace('.', ','))
        situacao = 'Conferir' if aluno['cobertura_parcial'] else 'Completa'
        linhas.append([
            pvalor(aluno['matricula']),
            pvalor(aluno['nome']),
            pvalor(aluno['presentes'], central),
            pvalor(aluno['atrasados'], central),
            pvalor(aluno['ausentes'], central),
            pvalor(aluno['justificados'], central),
            pvalor(cobertura, central),
            pvalor(percentual, direita),
            pvalor(situacao, central),
        ])

    if not dados['alunos']:
        linhas.append([pvalor('Nenhum aluno encontrado no período'),
                      *[pvalor('-', central) for _ in range(8)]])

    # Notas e assinatura compartilham uma faixa ao fim da tabela. Isso evita
    # a segunda página quase vazia em relatórios de turmas pequenas, sem
    # remover regras acadêmicas nem prejudicar a paginação de turmas grandes.
    nota_geral = (
        '<b>Legenda:</b> P = Presente; A = Atrasado; F = Ausente; J = Justificado. '
        '<b>Cobertura:</b> registros / aulas finalizadas. '
        '<b>Frequência:</b> (P + A) / registros × 100, somente com cobertura completa; '
        'Justificado não conta como presença. São consideradas apenas aulas '
        'finalizadas e as correções posteriores. Sem histórico de matrículas, '
        'ausência de registro não significa falta automática.'
    )
    assinatura = Paragraph(
        '________________________________<br/>'
        'Responsável pela conferência', nota
    )
    observacoes = Table([[
        Paragraph(nota_geral, nota), assinatura,
    ]], colWidths=[largura * .75, largura * .25], hAlign='LEFT')
    observacoes.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    # As duas últimas linhas e as observações seguem juntas para impedir
    # uma folha contendo somente legenda e assinatura.
    linhas.append([observacoes] + [''] * 8)
    proporcoes = [.13, .30, .055, .055, .055, .055, .12, .13, .10]
    tabela = LongTable(
        linhas,
        colWidths=[largura * p for p in proporcoes],
        repeatRows=1,
        hAlign='LEFT',
    )
    # Para turmas grandes, reduzimos somente o preenchimento vertical das
    # linhas, mantendo o tamanho da fonte e a legibilidade do documento.
    preenchimento_linha = 3.1 if len(dados['alunos']) >= 25 else 4.5
    estilos_tabela = [
        ('BACKGROUND', (0, 0), (-1, 0), azul),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), preenchimento_linha),
        ('BOTTOMPADDING', (0, 1), (-1, -1), preenchimento_linha),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 1), (-1, -2), .35, borda),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [branco, superficie]),
        ('SPAN', (0, -1), (-1, -1)),
        ('NOSPLIT', (0, -3), (-1, -1)),
        ('TOPPADDING', (0, -1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 0),
        ('LEFTPADDING', (0, -1), (-1, -1), 0),
        ('RIGHTPADDING', (0, -1), (-1, -1), 0),
    ]
    for indice, aluno in enumerate(dados['alunos'], start=1):
        if aluno['cobertura_parcial']:
            estilos_tabela.append(('BACKGROUND', (0, indice), (-1, indice),
                                  colors.HexColor('#FFF9ED')))
    tabela.setStyle(TableStyle(estilos_tabela))
    conteudo.append(tabela)

    emissao = datetime.now().strftime('%d/%m/%Y %H:%M')

    def decorar_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(vinho)
        canvas.rect(0, altura_pagina - 7 * mm, largura_pagina, 7 * mm, fill=1, stroke=0)

        canvas.setFillColor(azul)
        canvas.setFont('Helvetica-Bold', 13)
        canvas.drawString(18 * mm, altura_pagina - 21 * mm, 'SENTINELA')
        canvas.setFont('Helvetica', 8.5)
        canvas.setFillColor(cinza)
        canvas.drawString(51 * mm, altura_pagina - 21 * mm, '|  RELATÓRIOS ACADÊMICOS')
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(alerta_texto if incompletos else cinza)
        canvas.drawRightString(
            largura_pagina - 18 * mm, altura_pagina - 21 * mm,
            'PARA CONFERÊNCIA' if incompletos else 'REGISTROS COMPLETOS'
        )
        canvas.setStrokeColor(borda)
        canvas.setLineWidth(.6)
        canvas.line(18 * mm, altura_pagina - 26 * mm,
                    largura_pagina - 18 * mm, altura_pagina - 26 * mm)

        canvas.line(18 * mm, 18 * mm, largura_pagina - 18 * mm, 18 * mm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(cinza)
        canvas.drawString(18 * mm, 12 * mm,
                          f'Gerado pelo Sistema Sentinela  |  {emissao}')
        canvas.drawRightString(largura_pagina - 18 * mm, 12 * mm,
                               f'Página {doc.page}')
        canvas.restoreState()

    documento.build(conteudo, onFirstPage=decorar_pagina,
                    onLaterPages=decorar_pagina)
    buffer.seek(0)
    return buffer


def executar_consulta(id_turma, gerar_pdf=False):
    try:
        inicio, fim = validar_periodo()
    except ValueError as erro:
        return resposta_erro(str(erro), 400)

    conexao = obter_conexao()
    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None
    try:
        cursor = conexao.cursor(dictionary=True)
        usuario = validar_usuario(cursor)
        filtrar_acesso_turma(cursor, usuario, id_turma)
        dados = consultar_relatorio(cursor, id_turma, inicio, fim)

        if not gerar_pdf:
            resposta = jsonify(dados)
            resposta.headers['Cache-Control'] = 'private, no-store'
            return resposta

        buffer = criar_pdf(dados)
        nome = f"sentinela_frequencia_turma_{id_turma}_{inicio:%Y%m%d}_{fim:%Y%m%d}.pdf"
        resposta = send_file(
            buffer, mimetype='application/pdf',
            as_attachment=request.args.get('download') == '1',
            download_name=nome,
        )
        resposta.headers['Cache-Control'] = 'private, no-store'
        return resposta

    except PermissionError as erro:
        return resposta_erro(str(erro), 403)
    except LookupError as erro:
        return resposta_erro(str(erro), 404)
    except RuntimeError as erro:
        return resposta_erro(str(erro), 409)
    except ValueError as erro:
        return resposta_erro(str(erro), 422)
    except Error:
        return resposta_erro('Erro ao consultar os registros de frequência.', 500)
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


@relatorios_bp.get('/api/relatorios/turmas')
def listar_turmas_relatorios():
    conexao = obter_conexao()
    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None
    try:
        cursor = conexao.cursor(dictionary=True)
        usuario = validar_usuario(cursor)
        resposta = jsonify({'turmas': listar_turmas_permitidas(cursor, usuario)})
        resposta.headers['Cache-Control'] = 'private, no-store'
        return resposta
    except PermissionError as erro:
        return resposta_erro(str(erro), 403)
    except Error:
        return resposta_erro('Erro ao listar turmas.', 500)
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


@relatorios_bp.get('/api/relatorios/turmas/<int:id_turma>/frequencia')
def consultar_frequencia_turma(id_turma):
    return executar_consulta(id_turma)


@relatorios_bp.get('/api/relatorios/turmas/<int:id_turma>/frequencia.pdf')
def baixar_frequencia_turma(id_turma):
    return executar_consulta(id_turma, gerar_pdf=True)


# Relatório individual. Reutiliza autenticação, filtros e política da v0.5.0.
def listar_alunos_permitidos(cursor, id_turma):
    '''Alunos da turma atual e alunos com presença histórica em aulas da turma.'''
    cursor.execute('''
        SELECT al.id_aluno AS id, al.nome, al.matricula,
               al.status AS status_aluno
        FROM aluno al
        WHERE al.id_turma = %s
           OR EXISTS (
               SELECT 1
               FROM presenca p
               INNER JOIN aula a ON a.id_aula = p.id_aula
               WHERE p.id_aluno = al.id_aluno
                 AND a.id_turma = %s
                 AND a.status = 'Finalizada'
           )
        ORDER BY al.nome, al.id_aluno
    ''', (id_turma, id_turma))
    return cursor.fetchall()


def consultar_relatorio_individual(cursor, id_turma, id_aluno, inicio, fim):
    '''Histórico de aulas finalizadas sem inferir matrícula, transferência ou faltas.'''
    cursor.execute('''
        SELECT t.id_turma, t.nome AS turma, t.periodo, t.ano_letivo,
               t.semestre, t.status AS status_turma, c.nome AS curso
        FROM turma t
        INNER JOIN curso c ON c.id_curso = t.id_curso
        WHERE t.id_turma = %s
    ''', (id_turma,))
    turma = cursor.fetchone()
    if turma is None:
        raise LookupError('Turma não encontrada.')

    # Não expõe dados de alunos de outras turmas por manipulação do URL.
    # Como não há tabela histórica de matrículas, também admitimos um aluno
    # transferido quando há registros efetivos da turma consultada.
    cursor.execute('''
        SELECT al.id_aluno AS id, al.nome, al.matricula,
               al.status AS status_aluno
        FROM aluno al
        WHERE al.id_aluno = %s
          AND (
              al.id_turma = %s
              OR EXISTS (
                  SELECT 1
                  FROM presenca p
                  INNER JOIN aula a ON a.id_aula = p.id_aula
                  WHERE p.id_aluno = al.id_aluno
                    AND a.id_turma = %s
                    AND a.status = 'Finalizada'
              )
          )
    ''', (id_aluno, id_turma, id_turma))
    aluno = cursor.fetchone()
    if aluno is None:
        raise LookupError('Aluno não encontrado nos vínculos ou registros desta turma.')

    cursor.execute('''
        SELECT a.id_aula, a.data_aula, a.horario_inicio, a.horario_fim,
               pr.nome AS professor, amb.nome AS ambiente,
               p.id_presenca, p.status AS status_presenca,
               p.origem AS origem
        FROM aula a
        INNER JOIN professor pr ON pr.id_professor = a.id_professor
        INNER JOIN ambiente amb ON amb.id_ambiente = a.id_ambiente
        LEFT JOIN presenca p
          ON p.id_aula = a.id_aula AND p.id_aluno = %s
        WHERE a.id_turma = %s
          AND a.data_aula BETWEEN %s AND %s
          AND a.status = 'Finalizada'
        ORDER BY a.data_aula, a.horario_inicio, a.id_aula
    ''', (id_aluno, id_turma, inicio, fim))
    registros = cursor.fetchall()
    if not registros:
        raise ValueError('Não existem aulas finalizadas nessa turma e nesse período.')

    totais = {'Presente': 0, 'Atrasado': 0, 'Ausente': 0, 'Justificado': 0}
    aulas = []
    sem_registro = 0
    for registro in registros:
        situacao = registro['status_presenca']
        if situacao == 'Pendente':
            raise RuntimeError(
                'Existe presença pendente deste aluno em aula finalizada. '
                'Regularize o registro antes de emitir o relatório.'
            )
        if situacao is None:
            sem_registro += 1
            situacao = 'Sem registro'
        elif situacao in totais:
            totais[situacao] += 1
        else:
            raise RuntimeError('Situação de presença não reconhecida. Confira os registros.')

        data_aula = registro['data_aula']
        if isinstance(data_aula, (date, datetime)):
            data_aula = data_aula.isoformat()[:10]

        def horario(valor):
            if hasattr(valor, 'strftime'):
                return valor.strftime('%H:%M')
            if hasattr(valor, 'total_seconds'):  # mysql-connector: TIME -> timedelta
                segundos = int(valor.total_seconds())
                return f'{segundos // 3600:02d}:{(segundos % 3600) // 60:02d}'
            return str(valor)[:5]

        aulas.append({
            'id_aula': registro['id_aula'],
            'data': data_aula,
            'horario_inicio': horario(registro['horario_inicio']),
            'horario_fim': horario(registro['horario_fim']),
            'professor': registro['professor'],
            'ambiente': registro['ambiente'],
            'status': situacao,
            'origem': registro['origem'] if registro['id_presenca'] is not None else None,
        })

    total_aulas = len(aulas)
    total_registros = total_aulas - sem_registro
    conferencia = sem_registro > 0
    frequencia = (None if conferencia else round(
        100 * (totais['Presente'] + totais['Atrasado']) / total_registros, 2
    ))

    return {
        'turma': turma,
        'aluno': aluno,
        'periodo': {'inicio': inicio.isoformat(), 'fim': fim.isoformat()},
        'aulas_finalizadas': total_aulas,
        'resumo': {
            'presentes': totais['Presente'],
            'atrasados': totais['Atrasado'],
            'ausentes': totais['Ausente'],
            'justificados': totais['Justificado'],
            'aulas_com_registro': total_registros,
            'registros_faltantes': sem_registro,
            'frequencia_percentual': frequencia,
            'cobertura_parcial': conferencia,
        },
        'aulas': aulas,
        'criterios': {
            'aulas': 'Somente aulas finalizadas no período selecionado.',
            'horario': 'O horário apresentado é o da aula, não o horário de leitura RFID.',
            'frequencia': 'Presente e Atrasado contam como comparecimento.',
            'justificado': 'Justificado não equivale automaticamente a presença.',
            'sem_registro': ('Aula sem presença cadastrada não equivale a falta. '
                             'Cobertura parcial torna o percentual inconclusivo.'),
        },
    }


def criar_pdf_individual(dados):
    '''PDF A4 vertical com resumo e detalhamento por aula, inclusive multipágina.'''
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    azul = colors.HexColor('#233047')
    vinho = colors.HexColor('#AA2635')
    cinza = colors.HexColor('#667085')
    borda = colors.HexColor('#E5E9EF')
    superficie = colors.HexColor('#F5F7FA')
    alerta = colors.HexColor('#FFF4DF')
    largura_pagina, altura_pagina = A4
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=17 * mm, rightMargin=17 * mm,
        topMargin=30 * mm, bottomMargin=21 * mm,
        title='Sentinela | Frequência individual do aluno',
        author='Sistema Sentinela',
    )
    largura = documento.width
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle('IndTitulo', parent=estilos['Heading1'],
                             fontName='Helvetica-Bold', fontSize=17, leading=21,
                             textColor=azul, spaceAfter=3 * mm)
    subtitulo = ParagraphStyle('IndSub', parent=estilos['Normal'],
                                fontSize=9, leading=12, textColor=cinza)
    meta = ParagraphStyle('IndMeta', parent=estilos['Normal'],
                           fontSize=9, leading=13, textColor=azul)
    rotulo = ParagraphStyle('IndRot', parent=estilos['Normal'],
                             fontSize=7, leading=10, textColor=cinza)
    numero = ParagraphStyle('IndNum', parent=estilos['Normal'],
                             fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=azul)
    celula = ParagraphStyle('IndCel', parent=estilos['Normal'],
                             fontSize=7.4, leading=10, textColor=azul)
    central = ParagraphStyle('IndCentro', parent=celula, alignment=TA_CENTER)
    cabecalho = ParagraphStyle('IndCab', parent=central, fontName='Helvetica-Bold',
                                fontSize=7.2, leading=9.5, textColor=colors.white)
    nota = ParagraphStyle('IndNota', parent=estilos['Normal'], fontSize=8,
                           leading=11.5, textColor=cinza)

    def cel(v, estilo=celula):
        return Paragraph(escape(str(v if v is not None else '-')), estilo)

    def campo(chave, valor):
        return Paragraph(
            f'<font color="#667085" size="8">{escape(chave.upper())}</font><br/>'
            f'<b>{escape(str(valor))}</b>', meta
        )

    def ptdata(iso):
        return date.fromisoformat(iso).strftime('%d/%m/%Y')

    r = dados['resumo']
    total = dados['aulas_finalizadas']
    percentual = 'N/D' if r['frequencia_percentual'] is None else (
        f"{r['frequencia_percentual']:.2f}%".replace('.', ',')
    )
    conteudo = [
        Paragraph('Relatório individual de frequência', titulo),
        Paragraph('Histórico das chamadas finalizadas no período consultado.', subtitulo),
        Spacer(1, 5 * mm),
    ]
    info = Table([
        [campo('Aluno', dados['aluno']['nome']), campo('Matrícula', dados['aluno']['matricula'])],
        [campo('Curso / turma', f"{dados['turma']['curso']} / {dados['turma']['turma']}"),
         campo('Ano letivo / turno', f"{dados['turma']['ano_letivo']} / {dados['turma']['periodo']}")],
        [campo('Período consultado', f"{ptdata(dados['periodo']['inicio'])} a {ptdata(dados['periodo']['fim'])}"),
         campo('Aulas finalizadas', total)],
    ], colWidths=[largura * .63, largura * .37])
    info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), superficie),
        ('BOX', (0, 0), (-1, -1), .5, borda),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 11),
    ]))
    conteudo += [info, Spacer(1, 4 * mm)]

    indicadores = [
        ('PRESENTES', r['presentes']),
        ('ATRASADOS', r['atrasados']),
        ('AUSENTES', r['ausentes']),
        ('JUSTIFICADOS', r['justificados']),
        ('FREQUÊNCIA', percentual),
    ]
    cards = Table([[
        [Paragraph(label, rotulo), Spacer(1, 2 * mm), Paragraph(str(valor), numero)]
        for label, valor in indicadores
    ]], colWidths=[largura / len(indicadores)] * len(indicadores))
    cards.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), .5, borda),
        ('INNERGRID', (0, 0), (-1, -1), .4, borda),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
    ]))
    conteudo += [cards, Spacer(1, 4 * mm)]

    if r['cobertura_parcial']:
        mensagem = (
            f'<b>PARA CONFERÊNCIA</b> | {r["registros_faltantes"]} aula(s) finalizada(s) '
            'sem presença cadastrada para este aluno. Não são faltas automáticas. '
            'A frequência permanece N/D até a regularização dos registros '
            'ou conferência do histórico acadêmico.'
        )
        caixa = Table([[Paragraph(mensagem, nota)]], colWidths=[largura])
        caixa.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), alerta),
            ('LINEBEFORE', (0, 0), (0, 0), 3, colors.HexColor('#D99627')),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        conteudo += [caixa, Spacer(1, 4 * mm)]

    conteudo.append(Paragraph('Histórico de aulas', ParagraphStyle(
        'IndSec', parent=estilos['Heading2'], fontName='Helvetica-Bold',
        fontSize=11, leading=14, textColor=azul, spaceBefore=0, spaceAfter=3 * mm,
    )))
    colunas = [
        'Data', 'Aula', 'Horário', 'Ambiente', 'Situação', 'Origem',
    ]
    linhas = [[Paragraph(escape(c), cabecalho) for c in colunas]]
    for aula in dados['aulas']:
        linhas.append([
            cel(ptdata(aula['data']), central),
            cel(f"#{aula['id_aula']}", central),
            cel(f"{aula['horario_inicio']}–{aula['horario_fim']}", central),
            cel(aula['ambiente']),
            cel(aula['status'], central),
            cel(aula['origem'], central),
        ])
    # Reúne os critérios e a assinatura na última linha da tabela, para que
    # o ReportLab não gere uma página contendo apenas a assinatura.
    criterios = Paragraph(
        f'<b>Cobertura:</b> {r["aulas_com_registro"]}/{total} aulas finalizadas. '
        'Presente e Atrasado contam como comparecimento; Justificado não '
        'equivale automaticamente a presença. Sem registro não é falta '
        'automática, e o percentual fica N/D quando há registros faltantes. '
        'O horário é o da aula, não o do bip RFID. '
        'O sistema não possui histórico de matrículas e transferências.', nota
    )
    assinatura = Paragraph(
        '________________________<br/>Responsável pela conferência', nota
    )
    observacoes = Table([[
        criterios, assinatura,
    ]], colWidths=[largura * .72, largura * .28])
    observacoes.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    linhas.append([observacoes] + [''] * 5)

    tabela = LongTable(
        linhas,
        colWidths=[largura * p for p in [.15, .095, .175, .245, .19, .145]],
        repeatRows=1,
    )
    # Preserva a fonte e reduz apenas o espaço vertical em listas maiores.
    preenchimento = 5.1 if len(dados['aulas']) >= 12 else 7
    estilo_tabela = [
        ('BACKGROUND', (0, 0), (-1, 0), azul),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, superficie]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 1), (-1, -1), preenchimento),
        ('BOTTOMPADDING', (0, 1), (-1, -1), preenchimento),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 1), (-1, -2), .35, borda),
        ('SPAN', (0, -1), (-1, -1)),
        # Inclui as duas últimas aulas com notas e assinatura na mesma página.
        ('NOSPLIT', (0, -3), (-1, -1)),
        ('TOPPADDING', (0, -1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 0),
        ('LEFTPADDING', (0, -1), (-1, -1), 0),
        ('RIGHTPADDING', (0, -1), (-1, -1), 0),
    ]
    for i, aula in enumerate(dados['aulas'], 1):
        if aula['status'] == 'Sem registro':
            estilo_tabela.append(('BACKGROUND', (0, i), (-1, i), alerta))
    tabela.setStyle(TableStyle(estilo_tabela))
    conteudo.append(tabela)

    emissao = datetime.now().strftime('%d/%m/%Y %H:%M')

    def decorar(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(vinho)
        canvas.rect(0, altura_pagina - 7 * mm, largura_pagina, 7 * mm, fill=1, stroke=0)
        canvas.setFillColor(azul)
        canvas.setFont('Helvetica-Bold', 13)
        canvas.drawString(17 * mm, altura_pagina - 21 * mm, 'SENTINELA')
        canvas.setFillColor(cinza)
        canvas.setFont('Helvetica', 8.4)
        canvas.drawString(49 * mm, altura_pagina - 21 * mm, '|  RELATÓRIOS ACADÊMICOS')
        canvas.setFillColor(colors.HexColor('#855514') if r['cobertura_parcial'] else cinza)
        canvas.setFont('Helvetica-Bold', 7.5)
        canvas.drawRightString(largura_pagina - 17 * mm, altura_pagina - 25 * mm,
                               'PARA CONFERÊNCIA' if r['cobertura_parcial'] else 'REGISTROS COMPLETOS')
        canvas.setStrokeColor(borda)
        canvas.line(17 * mm, altura_pagina - 27 * mm,
                    largura_pagina - 17 * mm, altura_pagina - 27 * mm)
        canvas.line(17 * mm, 18 * mm, largura_pagina - 17 * mm, 18 * mm)
        canvas.setFillColor(cinza)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(17 * mm, 12 * mm, f'Gerado pelo Sistema Sentinela | {emissao}')
        canvas.drawRightString(largura_pagina - 17 * mm, 12 * mm, f'Página {doc.page}')
        canvas.restoreState()

    documento.build(conteudo, onFirstPage=decorar, onLaterPages=decorar)
    buffer.seek(0)
    return buffer


def executar_individual(id_turma, id_aluno, gerar_pdf=False):
    try:
        inicio, fim = validar_periodo()
    except ValueError as erro:
        return resposta_erro(str(erro), 400)

    conexao = obter_conexao()
    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)

    cursor = None
    try:
        cursor = conexao.cursor(dictionary=True)
        usuario = validar_usuario(cursor)
        filtrar_acesso_turma(cursor, usuario, id_turma)
        dados = consultar_relatorio_individual(cursor, id_turma, id_aluno, inicio, fim)
        if not gerar_pdf:
            resposta = jsonify(dados)
        else:
            nome = f'sentinela_frequencia_aluno_{id_aluno}_{inicio:%Y%m%d}_{fim:%Y%m%d}.pdf'
            resposta = send_file(
                criar_pdf_individual(dados), mimetype='application/pdf',
                as_attachment=request.args.get('download') == '1', download_name=nome,
            )
        resposta.headers['Cache-Control'] = 'private, no-store'
        return resposta
    except PermissionError as erro:
        return resposta_erro(str(erro), 403)
    except LookupError as erro:
        return resposta_erro(str(erro), 404)
    except RuntimeError as erro:
        return resposta_erro(str(erro), 409)
    except ValueError as erro:
        return resposta_erro(str(erro), 422)
    except Error:
        return resposta_erro('Erro ao consultar o histórico do aluno.', 500)
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


@relatorios_bp.get('/api/relatorios/turmas/<int:id_turma>/alunos')
def listar_alunos_relatorios(id_turma):
    conexao = obter_conexao()
    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)
    cursor = None
    try:
        cursor = conexao.cursor(dictionary=True)
        usuario = validar_usuario(cursor)
        filtrar_acesso_turma(cursor, usuario, id_turma)
        # Confirma turma válida, também no caso de lista de alunos vazia.
        cursor.execute('SELECT id_turma FROM turma WHERE id_turma = %s', (id_turma,))
        if cursor.fetchone() is None:
            raise LookupError('Turma não encontrada.')
        resposta = jsonify({'alunos': listar_alunos_permitidos(cursor, id_turma)})
        resposta.headers['Cache-Control'] = 'private, no-store'
        return resposta
    except PermissionError as erro:
        return resposta_erro(str(erro), 403)
    except LookupError as erro:
        return resposta_erro(str(erro), 404)
    except Error:
        return resposta_erro('Erro ao listar alunos da turma.', 500)
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


@relatorios_bp.get('/api/relatorios/turmas/<int:id_turma>/alunos/<int:id_aluno>/frequencia')
def consultar_frequencia_individual(id_turma, id_aluno):
    return executar_individual(id_turma, id_aluno)


@relatorios_bp.get('/api/relatorios/turmas/<int:id_turma>/alunos/<int:id_aluno>/frequencia.pdf')
def baixar_frequencia_individual(id_turma, id_aluno):
    return executar_individual(id_turma, id_aluno, gerar_pdf=True)
