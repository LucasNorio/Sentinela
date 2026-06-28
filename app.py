from flask import Flask, render_template, jsonify
from config import Config
from database import testar_conexao
from routes.alunos_routes import alunos_bp
from routes.professores_routes import professores_bp
from routes.academico_routes import academico_bp
from routes.ambientes_routes import ambientes_bp
from routes.leitores_routes import leitores_bp
from routes.registros_routes import registros_bp
from routes.dashboard_routes import dashboard_bp

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

app.config.from_object(Config)

app.register_blueprint(alunos_bp)
app.register_blueprint(professores_bp)
app.register_blueprint(academico_bp)
app.register_blueprint(ambientes_bp)
app.register_blueprint(leitores_bp)
app.register_blueprint(registros_bp)
app.register_blueprint(dashboard_bp)

@app.route('/')
def login():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/cadastro-alunos')
def cadastro_alunos():
    return render_template('cadastro-alunos.html')

@app.route('/cadastro-professores')
def cadastro_professores():
    return render_template('cadastro-professores.html')

@app.route('/historico')
def historico():
    return render_template('historico.html')

@app.route('/mapa')
def mapa():
    return render_template('mapa.html')

@app.route('/administracao')
def administracao():
    return render_template('administracao.html')

@app.route('/sobre')
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

@app.route('/gestao-academica')
def gestao_academica():
    return render_template('gestao-academica.html')

@app.route('/gestao-ambientes')
def gestao_ambientes():
    return render_template('gestao-ambientes.html')

@app.route('/gestao-leitores')
def gestao_leitores():
    return render_template('gestao-leitores.html')

if __name__ == '__main__':
    app.run(debug=True)