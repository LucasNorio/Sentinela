import mysql.connector
from mysql.connector import Error
from config import Config

def obter_conexao():
    try:
        conexao = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )

        return conexao

    except Error as erro:
        print(f'Erro ao conectar com o banco de dados: {erro}')
        return None

def testar_conexao():
    conexao = obter_conexao()

    if conexao is None:
        return False

    if conexao.is_connected():
        conexao.close()
        return True

    return False