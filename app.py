from flask import Flask, render_template, jsonify, session, redirect, request
from config import Config
from database import testar_conexao

from routes.auth_routes import auth_bp, login_obrigatorio
from routes.alunos_routes import alunos_bp
from routes.professores_routes import professores_bp
from routes.academico_routes import academico_bp
from routes.ambientes_routes import ambientes_bp
from routes.leitores_routes import leitores_bp
from routes.registros_routes import registros_bp
from routes.dashboard_routes import dashboard_bp
from routes.usuarios_routes import usuarios_bp

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

app.config.from_object(Config)
app.json.ensure_ascii = False

app.register_blueprint(auth_bp)
app.register_blueprint(alunos_bp)
app.register_blueprint(professores_bp)
app.register_blueprint(academico_bp)
app.register_blueprint(ambientes_bp)
app.register_blueprint(leitores_bp)
app.register_blueprint(registros_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(usuarios_bp)

TODOS_PERFIS = {
    'Administrador',
    'Coordenação',
    'Secretaria',
    'Professor'
}

PERFIS_GESTAO = {
    'Administrador',
    'Coordenação',
    'Secretaria'
}

PERFIS_ADMIN = {
    'Administrador'
}


PAGINAS_PERMISSOES = {
    '/home': TODOS_PERFIS,
    '/mapa': TODOS_PERFIS,
    '/historico': TODOS_PERFIS,
    '/sobre': TODOS_PERFIS,

    '/cadastro-alunos': PERFIS_GESTAO,
    '/cadastro-professores': PERFIS_GESTAO,
    '/gestao-academica': PERFIS_GESTAO,
    '/gestao-ambientes': PERFIS_GESTAO,
    '/gestao-leitores': PERFIS_GESTAO,

    '/administracao': PERFIS_ADMIN,
    '/gestao-usuarios': PERFIS_ADMIN,
}


APIS_PUBLICAS = {
    '/api/auth/login',
    '/api/auth/logout',
    '/api/auth/me',
    '/api/status'
}


def obter_usuario_sessao():
    return session.get('usuario')


def obter_perfil_sessao():
    usuario = obter_usuario_sessao()

    if not usuario:
        return None

    return usuario.get('perfil')


def api_permitida(caminho, metodo, perfil):
    if perfil == 'Administrador':
        return True

    if caminho.startswith('/api/dashboard'):
        return perfil in TODOS_PERFIS

    if caminho.startswith('/api/registros-rfid'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação'}

    if caminho.startswith('/api/alunos'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/professores'):
        if metodo == 'GET':
            return perfil in PERFIS_GESTAO

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/cursos'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/turmas'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/professor-turma'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/ambientes'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/leitores-rfid'):
        if metodo == 'GET':
            return perfil in TODOS_PERFIS

        return perfil in {'Coordenação', 'Secretaria'}

    if caminho.startswith('/api/usuarios'):
        return perfil == 'Administrador'

    return False


@app.before_request
def proteger_rotas():
    if request.path.startswith('/static/'):
        return None

    usuario = obter_usuario_sessao()
    perfil = obter_perfil_sessao()

    if request.path in PAGINAS_PERMISSOES:
        if not usuario:
            return redirect('/')

        if perfil not in PAGINAS_PERMISSOES[request.path]:
            return jsonify({
                'erro': 'Usuário sem permissão para acessar esta página.'
            }), 403

    if request.path.startswith('/api/') and request.path not in APIS_PUBLICAS:
        if not usuario:
            return jsonify({
                'erro': 'Usuário não autenticado.'
            }), 401

        if not api_permitida(request.path, request.method, perfil):
            return jsonify({
                'erro': 'Usuário sem permissão para esta ação.'
            }), 403

    return None


@app.route('/')
def login():
    if session.get('usuario'):
        return redirect('/home')

    return render_template('index.html')


@app.route('/sair')
def sair():
    session.clear()
    return redirect('/')


@app.route('/home')
@login_obrigatorio
def home():
    return render_template('home.html')


@app.route('/cadastro-alunos')
@login_obrigatorio
def cadastro_alunos():
    return render_template('cadastro-alunos.html')


@app.route('/cadastro-professores')
@login_obrigatorio
def cadastro_professores():
    return render_template('cadastro-professores.html')


@app.route('/gestao-academica')
@login_obrigatorio
def gestao_academica():
    return render_template('gestao-academica.html')


@app.route('/historico')
@login_obrigatorio
def historico():
    return render_template('historico.html')


@app.route('/mapa')
@login_obrigatorio
def mapa():
    return render_template('mapa.html')


@app.route('/gestao-ambientes')
@login_obrigatorio
def gestao_ambientes():
    return render_template('gestao-ambientes.html')


@app.route('/gestao-leitores')
@login_obrigatorio
def gestao_leitores():
    return render_template('gestao-leitores.html')


@app.route('/administracao')
@login_obrigatorio
def administracao():
    return render_template('administracao.html')

@app.route('/gestao-usuarios')
@login_obrigatorio
def gestao_usuarios():
    return render_template('gestao-usuarios.html')


@app.route('/sobre')
@login_obrigatorio
def sobre():
    return render_template('sobre.html')


@app.route('/api/status')
def status():
    banco_online = testar_conexao()

    return jsonify({
        'sistema': 'Sentinela',
        'backend': 'online',
        'banco_de_dados': 'online' if banco_online else 'offline'
    })


if __name__ == '__main__':
    app.run(debug=True)