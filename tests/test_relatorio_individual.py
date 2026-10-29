"""Testes do relatório individual sem dependência do MySQL em execução.

python -m unittest discover -s tests -v
"""
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from flask import Flask
from routes.relatorios_routes import (
    consultar_relatorio_individual, criar_pdf_individual,
    listar_alunos_permitidos, relatorios_bp,
)


class CursorIndividual:
    def __init__(self, registros=None, usuario=None, permitido=True,
                 aluno_existe=True, turma_existe=True):
        self.registros = registros if registros is not None else [registro('Presente')]
        self.usuario = usuario or {
            'id_usuario': 1, 'id_professor': 3,
            'perfil': 'Professor', 'status': 'Ativo',
        }
        self.permitido = permitido
        self.aluno_existe = aluno_existe
        self.turma_existe = turma_existe
        self.sql = ''
        self.params = None
        self.consultas = []
        self.closed = False

    def execute(self, sql, params=None):
        self.sql = ' '.join(sql.split())
        self.params = params
        self.consultas.append((self.sql, params))

    def fetchone(self):
        sql = self.sql
        if 'FROM usuario' in sql:
            return self.usuario
        if 'FROM professor_turma' in sql:
            return {'permitido': 1} if self.permitido else None
        if sql.startswith('SELECT id_turma FROM turma'):
            return {'id_turma': 7} if self.turma_existe else None
        if 'SELECT t.id_turma' in sql:
            return {
                'id_turma': 7, 'turma': 'DS-2026-A', 'periodo': 'Manhã',
                'ano_letivo': 2026, 'semestre': 2, 'status_turma': 'Ativa',
                'curso': 'Desenvolvimento de Sistemas',
            } if self.turma_existe else None
        if 'FROM aluno al' in sql:
            return {'id': 10, 'nome': 'João de Souza',
                    'matricula': '2026001', 'status_aluno': 'Ativo'} if self.aluno_existe else None
        raise AssertionError('Consulta fetchone não prevista: ' + sql)

    def fetchall(self):
        if 'FROM aula a' in self.sql:
            return self.registros
        if 'FROM aluno al' in self.sql:
            return [{'id': 10, 'nome': 'João de Souza',
                     'matricula': '2026001', 'status_aluno': 'Ativo'}]
        raise AssertionError('Consulta fetchall não prevista: ' + self.sql)

    def close(self):
        self.closed = True


class ConexaoIndividual:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.closed = False

    def cursor(self, dictionary=False):
        assert dictionary
        return self.cursor_obj

    def close(self):
        self.closed = True


def registro(status, id_aula=1, data=date(2026, 10, 20)):
    return {
        'id_aula': id_aula,
        'data_aula': data,
        'horario_inicio': timedelta(hours=8),
        'horario_fim': timedelta(hours=9, minutes=30),
        'professor': 'Maria da Silva',
        'ambiente': 'Laboratório de Informática',
        'id_presenca': None if status is None else id_aula,
        'status_presenca': status,
        'origem': 'RFID' if status is not None else None,
    }


class TestRelatorioIndividual(unittest.TestCase):
    def consultar(self, registros, **kwargs):
        return consultar_relatorio_individual(
            CursorIndividual(registros, **kwargs), 7, 10,
            date(2026, 10, 1), date(2026, 10, 22),
        )

    def test_frequencia_com_atraso_e_justificado(self):
        dados = self.consultar([
            registro('Presente', 1), registro('Atrasado', 2),
            registro('Ausente', 3), registro('Justificado', 4),
        ])
        self.assertEqual(dados['resumo']['frequencia_percentual'], 50.0)
        self.assertEqual(dados['resumo']['justificados'], 1)
        self.assertEqual(dados['resumo']['registros_faltantes'], 0)
        self.assertEqual(dados['aulas'][0]['horario_inicio'], '08:00')

    def test_sem_registro_nao_inventa_falta(self):
        dados = self.consultar([registro('Presente', 1), registro(None, 2)])
        self.assertIsNone(dados['resumo']['frequencia_percentual'])
        self.assertEqual(dados['resumo']['ausentes'], 0)
        self.assertEqual(dados['resumo']['registros_faltantes'], 1)
        self.assertEqual(dados['aulas'][1]['status'], 'Sem registro')
        self.assertIsNone(dados['aulas'][1]['origem'])

    def test_todas_sem_registro(self):
        dados = self.consultar([registro(None, 1), registro(None, 2)])
        self.assertIsNone(dados['resumo']['frequencia_percentual'])
        self.assertEqual(dados['resumo']['aulas_com_registro'], 0)

    def test_pendente_interrompe_emissao(self):
        with self.assertRaisesRegex(RuntimeError, 'pendente'):
            self.consultar([registro('Pendente')])

    def test_sem_aulas_finalizadas(self):
        with self.assertRaisesRegex(ValueError, 'Não existem aulas finalizadas'):
            self.consultar([])

    def test_aluno_fora_da_turma_nao_acessivel(self):
        with self.assertRaises(LookupError):
            self.consultar([registro('Presente')], aluno_existe=False)

    def test_consulta_isola_presenca_do_aluno_e_turma(self):
        cursor = CursorIndividual()
        consultar_relatorio_individual(cursor, 7, 10, date(2026, 10, 1), date(2026, 10, 22))
        self.assertTrue(any('p.id_aluno = %s' in sql and 'LEFT JOIN presenca' in sql
                            and params == (10, 7, date(2026, 10, 1), date(2026, 10, 22))
                            for sql, params in cursor.consultas))
        self.assertTrue(any('EXISTS' in sql and params == (10, 7, 7)
                            for sql, params in cursor.consultas))

    def test_pdf_acentuacao_e_multiplas_paginas(self):
        registros = [registro('Presente', i) for i in range(1, 71)]
        dados = self.consultar(registros)
        arquivo = criar_pdf_individual(dados).getvalue()
        self.assertTrue(arquivo.startswith(b'%PDF-'))
        self.assertGreater(len(arquivo), 4000)
        import re
        self.assertGreater(len(re.findall(rb'/Type\s*/Page\b', arquivo)), 1)

    def test_pdf_quinze_aulas_nao_deixa_rodape_isolado(self):
        import re
        dados = self.consultar([registro('Presente', i) for i in range(1, 16)])
        pdf = criar_pdf_individual(dados).getvalue()
        self.assertEqual(len(re.findall(rb'/Type\s*/Page\b', pdf)), 1)

    def test_pdf_quarenta_aulas_sem_pagina_extra_de_assinatura(self):
        import re
        dados = self.consultar([registro('Presente', i) for i in range(1, 41)])
        pdf = criar_pdf_individual(dados).getvalue()
        self.assertEqual(len(re.findall(rb'/Type\s*/Page\b', pdf)), 2)

    def test_pdf_parcial_emite_para_conferencia(self):
        dados = self.consultar([registro('Presente', 1), registro(None, 2)])
        pdf = criar_pdf_individual(dados).getvalue()
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertTrue(dados['resumo']['cobertura_parcial'])
        self.assertIsNone(dados['resumo']['frequencia_percentual'])

    def test_lista_alunos_inclui_historicos(self):
        cursor = CursorIndividual()
        lista = listar_alunos_permitidos(cursor, 7)
        self.assertEqual(lista[0]['id'], 10)
        self.assertIn('EXISTS', cursor.sql)
        self.assertEqual(cursor.params, (7, 7))

    def test_rota_impede_professor_sem_vinculo(self):
        flask_app = Flask(__name__)
        flask_app.secret_key = 'apenas-teste'
        flask_app.register_blueprint(relatorios_bp)
        cursor = CursorIndividual(permitido=False)
        with patch('routes.relatorios_routes.obter_conexao', return_value=ConexaoIndividual(cursor)):
            with flask_app.test_client() as cliente:
                with cliente.session_transaction() as sessao:
                    sessao['usuario'] = {'id': 1}
                resposta = cliente.get('/api/relatorios/turmas/7/alunos/10/frequencia?inicio=2026-10-01&fim=2026-10-22')
        self.assertEqual(resposta.status_code, 403)

    def test_rota_individual_resposta_json_e_pdf(self):
        flask_app = Flask(__name__)
        flask_app.secret_key = 'apenas-teste'
        flask_app.register_blueprint(relatorios_bp)
        with flask_app.test_client() as cliente:
            with cliente.session_transaction() as sessao:
                sessao['usuario'] = {'id': 1}
            for caminho, mimetype in [
                ('/api/relatorios/turmas/7/alunos/10/frequencia', 'application/json'),
                ('/api/relatorios/turmas/7/alunos/10/frequencia.pdf', 'application/pdf'),
                ('/api/relatorios/turmas/7/alunos', 'application/json'),
            ]:
                with patch('routes.relatorios_routes.obter_conexao', return_value=ConexaoIndividual(CursorIndividual())):
                    resposta = cliente.get(caminho + '?inicio=2026-10-01&fim=2026-10-22')
                self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True)[:400] if resposta.mimetype == 'application/json' else '')
                self.assertEqual(resposta.mimetype, mimetype)
                self.assertEqual(resposta.headers['Cache-Control'], 'private, no-store')

if __name__ == '__main__':
    unittest.main()
