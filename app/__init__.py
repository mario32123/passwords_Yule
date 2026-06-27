from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para continuar.'
login_manager.login_message_category = 'warning'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config['ENCRYPTION_KEY']:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        app.config['ENCRYPTION_KEY'] = key
        print('\n' + '='*60)
        print('ADVERTENCIA: No se encontró ENCRYPTION_KEY.')
        print(f'Clave temporal generada: {key}')
        print('Guarda esta clave como variable de entorno ENCRYPTION_KEY')
        print('Los datos cifrados se perderán si reinicias sin ella.')
        print('='*60 + '\n')

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        _seed_data()

    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        print('=== ERROR 500 ===')
        print(traceback.format_exc())
        print('================')
        db.session.rollback()
        from flask import render_template as rt
        return rt('error500.html'), 500

    return app


def _seed_data():
    from app.models import User, Site

    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', email='admin@gestorpass.local', role='admin')
        admin.set_password('Admin123!')
        db.session.add(admin)
        print('Usuario admin creado. Contraseña inicial: Admin123!')
        print('Cambia esta contraseña inmediatamente desde Administración > Usuarios.')

    sitios_default = [
        ('DIAN',                   'https://www.dian.gov.co',             'impuestos'),
        ('MUISCA - DIAN',          'https://muisca.dian.gov.co',          'impuestos'),
        ('Secretaría Hacienda',    '',                                     'impuestos'),
        ('Aportes en Línea',       'https://www.aportesenlinea.com/independientes/inicio', 'aportes'),
        ('Mi Planilla',            'https://www.miplanilla.com',           'aportes'),
        ('PILA',                   '',                                     'aportes'),
        ('Cámara de Comercio CCB', 'https://www.ccb.org.co',              'camara'),
        ('RUES',                   'https://www.rues.org.co',             'camara'),
        ('Confecámaras',           'https://www.confecamaras.org.co',     'camara'),
        ('Gmail',                  'https://gmail.com',                   'correo'),
        ('Outlook / Hotmail',      'https://outlook.com',                 'correo'),
        ('Yahoo Mail',             'https://mail.yahoo.com',              'correo'),
        ('Bancolombia',            'https://www.bancolombia.com',         'banco'),
        ('Davivienda',             'https://www.davivienda.com',          'banco'),
        ('Banco de Bogotá',        'https://www.bancodebogota.com',       'banco'),
        ('BBVA Colombia',          'https://www.bbva.com.co',             'banco'),
    ]

    for nombre, url, categoria in sitios_default:
        existing = Site.query.filter_by(name=nombre).first()
        if not existing:
            db.session.add(Site(name=nombre, url=url, category=categoria))
        elif existing.url != url and url:
            existing.url = url  # actualiza URL si cambió

    db.session.commit()
