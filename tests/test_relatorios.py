"""Testes isolados do relatório por turma; não exigem MySQL em execução.

Execute na raiz do Sentinela com seu .venv ativo:
    python -m unittest discover -s tests -v
"""
import unittest
from datetime import date

from routes.relatorios_routes import consultar_relatorio, criar_pdf


class CursorFalso:
    def __init__(self, aulas=20, pendentes=0, presencas=None, alunos=None):
        self.aulas = aulas
        self.pendentes = pendentes
        self.presencas = presencas or []
        self.alunos = alunos or []
        self.sql = ''

    def execute(self, sql, parametros=None):
        self.sql = ' '.join(sql.split())

    def fetchone(self):
        if 'SELECT t.id_turma' in self.sql:
            return {
                'id_turma': 1,
                'turma': 'DS-2026-A',
                'curso': 'Desenvolvimento de Sistemas',
                'periodo': 'Manhã',
                'ano_letivo': 2026,
                'semestre': 2,
                'status_turma': 'Ativa',
            }
        if "p.status = 'Pendente'" in self.sql:
            return {'total': self.pendentes}
        if "a.status = 'Finalizada'" in self.sql and 'COUNT(*)' in self.sql:
            return {'total': self.aulas}
        raise AssertionError(f'Consulta inesperada: {self.sql}')

    def fetchall(self):
        if 'FROM presenca p' in self.sql:
            return self.presencas
        if 'FROM aluno' in self.sql:
            return self.alunos
        raise AssertionError(f'Consulta inesperada: {self.sql}')


def aluno(id_aluno):
    return {
        'id': id_aluno, 'nome': f'Aluno {id_aluno}',
        'matricula': f'2026{id_aluno:04d}', 'status_aluno': 'Ativo',
    }


def resumo(id_aluno, presentes=0, atrasados=0, ausentes=0, justificados=0):
    return dict(
        aluno(id_aluno),
        aulas_com_registro=presentes + atrasados + ausentes + justificados,
        presentes=presentes, atrasados=atrasados,
        ausentes=ausentes, justificados=justificados,
    )


class TestRelatorioTurma(unittest.TestCase):
    def consultar(self, cursor):
        return consultar_relatorio(cursor, 1, date(2026, 10, 1), date(2026, 10, 22))

    def test_frequencia_completa_considera_atrasos_e_justificativas(self):
        cursor = CursorFalso(
            aulas=20,
            presencas=[resumo(1, presentes=15, atrasados=2, ausentes=2, justificados=1)],
            alunos=[aluno(1)],
        )
        dados = self.consultar(cursor)
        self.assertEqual(dados['alunos'][0]['frequencia_percentual'], 85.0)
        self.assertEqual(dados['alunos_cobertura_completa'], 1)
        self.assertEqual(dados['alunos_cobertura_parcial'], 0)

    def test_cobertura_parcial_nao_publica_cem_por_cento(self):
        cursor = CursorFalso(
            aulas=20,
            presencas=[resumo(1, presentes=1)],
            alunos=[aluno(1)],
        )
        dados = self.consultar(cursor)
        self.assertIsNone(dados['alunos'][0]['frequencia_percentual'])
        self.assertTrue(dados['alunos'][0]['cobertura_parcial'])
        self.assertEqual(dados['alunos'][0]['registros_faltantes'], 19)

    def test_aluno_sem_registros_nao_e_falta_automatica(self):
        cursor = CursorFalso(aulas=20, alunos=[aluno(1)])
        dados = self.consultar(cursor)
        self.assertEqual(dados['alunos'][0]['ausentes'], 0)
        self.assertIsNone(dados['alunos'][0]['frequencia_percentual'])
        self.assertTrue(dados['alunos'][0]['cobertura_parcial'])

    def test_pendencia_bloqueia_relatorio(self):
        with self.assertRaisesRegex(RuntimeError, 'pendentes'):
            self.consultar(CursorFalso(aulas=20, pendentes=1))

    def test_sem_aulas_finalizadas_nao_gera_relatorio(self):
        with self.assertRaisesRegex(ValueError, 'Não existem aulas finalizadas'):
            self.consultar(CursorFalso(aulas=0))

    def test_pdf_seis_alunos_com_cobertura_parcial_cabe_em_uma_pagina(self):
        import re
        registros = [resumo(1, presentes=4, ausentes=1)]
        registros += [resumo(i, presentes=3, ausentes=1) for i in range(2, 7)]
        dados = self.consultar(CursorFalso(
            aulas=5,
            presencas=registros,
            alunos=[aluno(i) for i in range(1, 7)],
        ))
        pdf = criar_pdf(dados).getvalue()
        self.assertEqual(len(re.findall(rb'/Type\s*/Page\b', pdf)), 1)
        self.assertEqual(dados['alunos_cobertura_parcial'], 5)

    def test_pdf_turma_grande_distribui_tabela_e_assinatura(self):
        import re
        registros = [resumo(i, presentes=4, ausentes=1) for i in range(1, 31)]
        dados = self.consultar(CursorFalso(
            aulas=5,
            presencas=registros,
            alunos=[aluno(i) for i in range(1, 31)],
        ))
        pdf = criar_pdf(dados).getvalue()
        self.assertEqual(len(re.findall(rb'/Type\s*/Page\b', pdf)), 2)

    def test_geracao_pdf_com_acento_e_situacao_parcial(self):
        cursor = CursorFalso(
            aulas=20,
            presencas=[resumo(1, presentes=1)],
            alunos=[aluno(1)],
        )
        dados = self.consultar(cursor)
        pdf = criar_pdf(dados).getvalue()
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertGreater(len(pdf), 2000)


if __name__ == '__main__':
    unittest.main()
