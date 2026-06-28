from flask import Blueprint, jsonify, request
from mysql.connector import IntegrityError, Error
from database import obter_conexao
import re

professores_bp = Blueprint('professores_bp', __name__)

STATUS_PROFESSOR_VALIDOS = {'Ativo', 'Inativo'}

def resposta_erro(mensagem, status=400):
    return jsonify({'erro': mensagem}), status

def validar_professor(dados):
    nome = str(dados.get('nome', '')).strip()
    email = str(dados.get('email', '')).strip().lower()
    registro_professor = str(dados.get('registro_professor', '')).strip()
    area = str(dados.get('area', '')).strip()
    telefone = str(dados.get('telefone', '')).strip()
    telefone_numeros = re.sub(r'\D', '', telefone)
    status = dados.get('status', 'Ativo')

    if telefone_numeros == '':
        telefone = None
    elif len(telefone_numeros) == 10:
        telefone = f'({telefone_numeros[:2]}) {telefone_numeros[2:6]}-{telefone_numeros[6:]}'
    elif len(telefone_numeros) == 11:
        telefone = f'({telefone_numeros[:2]}) {telefone_numeros[2:7]}-{telefone_numeros[7:]}'
    else:
        return None, 'Telefone inválido. Use o formato com DDD.'

    if not nome:
        return None, 'O nome do professor é obrigatório.'
    
    if not email:
        return None, 'O email do professor é obrigatório.'
    
    if not registro_professor:
        return None, 'O registro do professor é obrigatório.'
    
    if not area:
        return None, 'A área do professor é obrigatória.'
    
    if status not in STATUS_PROFESSOR_VALIDOS:
        return None, 'Status inválido.'
    
    return {
        'nome': nome,
        'email': email,
        'registro_professor': registro_professor,
        'area': area,
        'telefone': telefone,
        'status': status
    }, None

@professores_bp.get('/api/professores')
def listar_professores():
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)
    
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id_professor AS id,
                nome,
                email,
                registro_professor,
                area,
                telefone,
                status,
                DATE_FORMAT(criado_em, '%Y-%m-%d %H:%i:%s') AS criado_em,
                DATE_FORMAT(inativado_em, '%Y-%m-%d %H:%i:%s') AS inativado_em,
                motivo_inativacao
            FROM professor
            ORDER BY nome       
        """)

        return jsonify(cursor.fetchall())
    
    except Error as erro:
        return resposta_erro(f'Erro ao listar professores: {erro}', 500)
    
    finally:
        if cursor:
            cursor.close()

        conexao.close()

@professores_bp.post('/api/professores')
def cadastrar_professor():
    dados = request.get_json(silent=True) or {}
    professor, erro_validacao = validar_professor(dados)

    if erro_validacao:
        return resposta_erro(erro_validacao)
    
    conexao = obter_conexao()

    if conexao is None:
        return resposta_erro('Não foi possível conectar ao banco de dados.', 500)
    
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO professor
                (nome, email, registro_professor, area, telefone, status)
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """, (
            professor['nome'],
            professor['email'],
            professor['registro_professor'],
            professor['area'],
            professor['telefone'],
            professor['status'],
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Professor cadastrado com sucesso.',
            'id_professor': cursor.lastrowid
        }), 201
    
    except IntegrityError:
        conexao.rollback()
        return resposta_erro('E-mail ou registro do professor já cadastrado.', 409)
    
    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao cadastrar professor: {erro}', 500)
    
    finally:
        if cursor:
            cursor.close()

        conexao.close()

@professores_bp.put('/api/professores/<int:id_professor>')
def atualizar_professor(id_professor):
    dados = request.get_json(silent=True) or {}
    professor, erro_validacao = validar_professor(dados)

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
            SELECT id_professor
            FROM professor
            WHERE id_professor = %s
        """, (id_professor,))

        if cursor.fetchone() is None:
            conexao.rollback()
            return resposta_erro('Professor não encontrado.', 404) 
        
        cursor.execute("""
            UPDATE professor
            SET
                nome = %s,
                email = %s,
                registro_professor = %s,
                area = %s,
                telefone = %s,
                status = %s
            WHERE id_professor = %s
        """, (
            professor['nome'],
            professor['email'],
            professor['registro_professor'],
            professor['area'],
            professor['telefone'],
            professor['status'],
            id_professor
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Professor atualizado com sucesso.'
        })
    
    except IntegrityError:
        conexao.rollback()
        return resposta_erro('E-mail ou registro do professor já cadastrado.', 409)
    
    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao atualizar professor: {erro}', 500)
    
    finally:
        if cursor:
            cursor.close()

        conexao.close()

@professores_bp.patch('/api/professores/<int:id_professor>/inativar')
def inativar_professor(id_professor):
    dados = request.get_json(silent=True) or {}
    motivo = str(dados.get('motivo', 'Professor inativado pelo sistema.')).strip()

    if motivo == '':
        motivo = 'Professor inativado pelo sistema.'

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
        """, (id_professor,))

        professor = cursor.fetchone()

        if professor is None:
            conexao.rollback()
            return resposta_erro('Professor não encontrado.', 404)
        
        if professor['status'] == 'Inativo':
            conexao.rollback()
            return resposta_erro('Professor já está inativo.', 409)
        
        cursor.execute("""
            UPDATE professor
            SET
                status = 'Inativo',
                inativado_em = NOW(),
                motivo_inativacao = %s
            WHERE id_professor = %s
        """, (
            motivo,
            id_professor
        ))

        conexao.commit()

        return jsonify({
            'mensagem': 'Professor inativado com sucesso.'
        })
    
    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao inativar professor: {erro}', 500)
    
    finally:
        if cursor:
            cursor.close()

        conexao.close()

@professores_bp.patch('/api/professores/<int:id_professor>/reativar')
def reativar_professor(id_professor):
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
        """, (id_professor,))

        professor = cursor.fetchone()

        if professor is None:
            conexao.rollback()
            return resposta_erro('Professor não encontrado.', 404)
        
        if professor['status'] == 'Ativo':
            conexao.rollback()
            return resposta_erro('Professor já está ativo.', 409)
        
        cursor.execute("""
            UPDATE professor
            SET
                status = 'Ativo',
                inativado_em = NULL,
                motivo_inativacao = NULL
            WHERE id_professor = %s
        """, (id_professor,))

        conexao.commit()

        return jsonify({
            'mensagem': 'Professor reativado com sucesso.'
        })
    
    except Error as erro:
        conexao.rollback()
        return resposta_erro(f'Erro ao reativar professor: {erro}', 500)
    
    finally:
        if cursor:
            cursor.close()

        conexao.close()
