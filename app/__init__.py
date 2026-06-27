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
            existing.url = url

    db.session.commit()
    _seed_calendar_2026()


def _seed_calendar_2026():
    from app.models import TaxDeadline
    from datetime import date

    if TaxDeadline.query.filter_by(year=2026).first():
        return  # ya existe, no reinsertar

    # (tax_type, period_label, nit_digit, year, month, day)
    datos = [
        # ── Retención en la Fuente ─────────────────────────────────────
        ('retefuente','Enero 2026',      1,2026,2,10),('retefuente','Enero 2026',      2,2026,2,11),
        ('retefuente','Enero 2026',      3,2026,2,12),('retefuente','Enero 2026',      4,2026,2,13),
        ('retefuente','Enero 2026',      5,2026,2,16),('retefuente','Enero 2026',      6,2026,2,17),
        ('retefuente','Enero 2026',      7,2026,2,18),('retefuente','Enero 2026',      8,2026,2,19),
        ('retefuente','Enero 2026',      9,2026,2,20),('retefuente','Enero 2026',      0,2026,2,23),

        ('retefuente','Febrero 2026',    1,2026,3,10),('retefuente','Febrero 2026',    2,2026,3,11),
        ('retefuente','Febrero 2026',    3,2026,3,12),('retefuente','Febrero 2026',    4,2026,3,13),
        ('retefuente','Febrero 2026',    5,2026,3,16),('retefuente','Febrero 2026',    6,2026,3,17),
        ('retefuente','Febrero 2026',    7,2026,3,18),('retefuente','Febrero 2026',    8,2026,3,19),
        ('retefuente','Febrero 2026',    9,2026,3,20),('retefuente','Febrero 2026',    0,2026,3,24),

        ('retefuente','Marzo 2026',      1,2026,4,13),('retefuente','Marzo 2026',      2,2026,4,14),
        ('retefuente','Marzo 2026',      3,2026,4,15),('retefuente','Marzo 2026',      4,2026,4,16),
        ('retefuente','Marzo 2026',      5,2026,4,20),('retefuente','Marzo 2026',      6,2026,4,21),
        ('retefuente','Marzo 2026',      7,2026,4,22),('retefuente','Marzo 2026',      8,2026,4,23),
        ('retefuente','Marzo 2026',      9,2026,4,24),('retefuente','Marzo 2026',      0,2026,4,27),

        ('retefuente','Abril 2026',      1,2026,5,12),('retefuente','Abril 2026',      2,2026,5,13),
        ('retefuente','Abril 2026',      3,2026,5,14),('retefuente','Abril 2026',      4,2026,5,15),
        ('retefuente','Abril 2026',      5,2026,5,19),('retefuente','Abril 2026',      6,2026,5,20),
        ('retefuente','Abril 2026',      7,2026,5,21),('retefuente','Abril 2026',      8,2026,5,22),
        ('retefuente','Abril 2026',      9,2026,5,25),('retefuente','Abril 2026',      0,2026,5,26),

        ('retefuente','Mayo 2026',       1,2026,6,10),('retefuente','Mayo 2026',       2,2026,6,11),
        ('retefuente','Mayo 2026',       3,2026,6,12),('retefuente','Mayo 2026',       4,2026,6,16),
        ('retefuente','Mayo 2026',       5,2026,6,17),('retefuente','Mayo 2026',       6,2026,6,18),
        ('retefuente','Mayo 2026',       7,2026,6,19),('retefuente','Mayo 2026',       8,2026,6,22),
        ('retefuente','Mayo 2026',       9,2026,6,23),('retefuente','Mayo 2026',       0,2026,6,24),

        ('retefuente','Junio 2026',      1,2026,7, 9),('retefuente','Junio 2026',      2,2026,7,10),
        ('retefuente','Junio 2026',      3,2026,7,13),('retefuente','Junio 2026',      4,2026,7,14),
        ('retefuente','Junio 2026',      5,2026,7,15),('retefuente','Junio 2026',      6,2026,7,16),
        ('retefuente','Junio 2026',      7,2026,7,17),('retefuente','Junio 2026',      8,2026,7,21),
        ('retefuente','Junio 2026',      9,2026,7,22),('retefuente','Junio 2026',      0,2026,7,23),

        ('retefuente','Julio 2026',      1,2026,8,12),('retefuente','Julio 2026',      2,2026,8,13),
        ('retefuente','Julio 2026',      3,2026,8,14),('retefuente','Julio 2026',      4,2026,8,18),
        ('retefuente','Julio 2026',      5,2026,8,19),('retefuente','Julio 2026',      6,2026,8,20),
        ('retefuente','Julio 2026',      7,2026,8,21),('retefuente','Julio 2026',      8,2026,8,24),
        ('retefuente','Julio 2026',      9,2026,8,25),('retefuente','Julio 2026',      0,2026,8,26),

        ('retefuente','Agosto 2026',     1,2026,9, 9),('retefuente','Agosto 2026',     2,2026,9,10),
        ('retefuente','Agosto 2026',     3,2026,9,11),('retefuente','Agosto 2026',     4,2026,9,14),
        ('retefuente','Agosto 2026',     5,2026,9,15),('retefuente','Agosto 2026',     6,2026,9,16),
        ('retefuente','Agosto 2026',     7,2026,9,17),('retefuente','Agosto 2026',     8,2026,9,18),
        ('retefuente','Agosto 2026',     9,2026,9,21),('retefuente','Agosto 2026',     0,2026,9,22),

        ('retefuente','Septiembre 2026', 1,2026,10, 9),('retefuente','Septiembre 2026',2,2026,10,13),
        ('retefuente','Septiembre 2026', 3,2026,10,14),('retefuente','Septiembre 2026',4,2026,10,15),
        ('retefuente','Septiembre 2026', 5,2026,10,16),('retefuente','Septiembre 2026',6,2026,10,19),
        ('retefuente','Septiembre 2026', 7,2026,10,20),('retefuente','Septiembre 2026',8,2026,10,21),
        ('retefuente','Septiembre 2026', 9,2026,10,22),('retefuente','Septiembre 2026',0,2026,10,23),

        ('retefuente','Octubre 2026',    1,2026,11,11),('retefuente','Octubre 2026',   2,2026,11,12),
        ('retefuente','Octubre 2026',    3,2026,11,13),('retefuente','Octubre 2026',   4,2026,11,17),
        ('retefuente','Octubre 2026',    5,2026,11,18),('retefuente','Octubre 2026',   6,2026,11,19),
        ('retefuente','Octubre 2026',    7,2026,11,20),('retefuente','Octubre 2026',   8,2026,11,23),
        ('retefuente','Octubre 2026',    9,2026,11,24),('retefuente','Octubre 2026',   0,2026,11,25),

        ('retefuente','Noviembre 2026',  1,2026,12,10),('retefuente','Noviembre 2026', 2,2026,12,11),
        ('retefuente','Noviembre 2026',  3,2026,12,14),('retefuente','Noviembre 2026', 4,2026,12,15),
        ('retefuente','Noviembre 2026',  5,2026,12,16),('retefuente','Noviembre 2026', 6,2026,12,17),
        ('retefuente','Noviembre 2026',  7,2026,12,18),('retefuente','Noviembre 2026', 8,2026,12,21),
        ('retefuente','Noviembre 2026',  9,2026,12,22),('retefuente','Noviembre 2026', 0,2026,12,23),

        ('retefuente','Diciembre 2026',  1,2027,1,13),('retefuente','Diciembre 2026',  2,2027,1,14),
        ('retefuente','Diciembre 2026',  3,2027,1,15),('retefuente','Diciembre 2026',  4,2027,1,18),
        ('retefuente','Diciembre 2026',  5,2027,1,19),('retefuente','Diciembre 2026',  6,2027,1,20),
        ('retefuente','Diciembre 2026',  7,2027,1,21),('retefuente','Diciembre 2026',  8,2027,1,22),
        ('retefuente','Diciembre 2026',  9,2027,1,25),('retefuente','Diciembre 2026',  0,2027,1,26),

        # ── IVA Bimestral ──────────────────────────────────────────────
        ('iva_bimestral','Ene-Feb 2026', 1,2026,3,10),('iva_bimestral','Ene-Feb 2026', 2,2026,3,11),
        ('iva_bimestral','Ene-Feb 2026', 3,2026,3,12),('iva_bimestral','Ene-Feb 2026', 4,2026,3,13),
        ('iva_bimestral','Ene-Feb 2026', 5,2026,3,16),('iva_bimestral','Ene-Feb 2026', 6,2026,3,17),
        ('iva_bimestral','Ene-Feb 2026', 7,2026,3,18),('iva_bimestral','Ene-Feb 2026', 8,2026,3,19),
        ('iva_bimestral','Ene-Feb 2026', 9,2026,3,20),('iva_bimestral','Ene-Feb 2026', 0,2026,3,24),

        ('iva_bimestral','Mar-Abr 2026', 1,2026,5,12),('iva_bimestral','Mar-Abr 2026', 2,2026,5,13),
        ('iva_bimestral','Mar-Abr 2026', 3,2026,5,14),('iva_bimestral','Mar-Abr 2026', 4,2026,5,15),
        ('iva_bimestral','Mar-Abr 2026', 5,2026,5,19),('iva_bimestral','Mar-Abr 2026', 6,2026,5,20),
        ('iva_bimestral','Mar-Abr 2026', 7,2026,5,21),('iva_bimestral','Mar-Abr 2026', 8,2026,5,22),
        ('iva_bimestral','Mar-Abr 2026', 9,2026,5,25),('iva_bimestral','Mar-Abr 2026', 0,2026,5,26),

        ('iva_bimestral','May-Jun 2026', 1,2026,7, 9),('iva_bimestral','May-Jun 2026', 2,2026,7,10),
        ('iva_bimestral','May-Jun 2026', 3,2026,7,13),('iva_bimestral','May-Jun 2026', 4,2026,7,14),
        ('iva_bimestral','May-Jun 2026', 5,2026,7,15),('iva_bimestral','May-Jun 2026', 6,2026,7,16),
        ('iva_bimestral','May-Jun 2026', 7,2026,7,17),('iva_bimestral','May-Jun 2026', 8,2026,7,21),
        ('iva_bimestral','May-Jun 2026', 9,2026,7,22),('iva_bimestral','May-Jun 2026', 0,2026,7,23),

        ('iva_bimestral','Jul-Ago 2026', 1,2026,9, 9),('iva_bimestral','Jul-Ago 2026', 2,2026,9,10),
        ('iva_bimestral','Jul-Ago 2026', 3,2026,9,11),('iva_bimestral','Jul-Ago 2026', 4,2026,9,14),
        ('iva_bimestral','Jul-Ago 2026', 5,2026,9,15),('iva_bimestral','Jul-Ago 2026', 6,2026,9,16),
        ('iva_bimestral','Jul-Ago 2026', 7,2026,9,17),('iva_bimestral','Jul-Ago 2026', 8,2026,9,18),
        ('iva_bimestral','Jul-Ago 2026', 9,2026,9,21),('iva_bimestral','Jul-Ago 2026', 0,2026,9,22),

        ('iva_bimestral','Sep-Oct 2026', 1,2026,11,11),('iva_bimestral','Sep-Oct 2026',2,2026,11,12),
        ('iva_bimestral','Sep-Oct 2026', 3,2026,11,13),('iva_bimestral','Sep-Oct 2026',4,2026,11,17),
        ('iva_bimestral','Sep-Oct 2026', 5,2026,11,18),('iva_bimestral','Sep-Oct 2026',6,2026,11,19),
        ('iva_bimestral','Sep-Oct 2026', 7,2026,11,20),('iva_bimestral','Sep-Oct 2026',8,2026,11,23),
        ('iva_bimestral','Sep-Oct 2026', 9,2026,11,24),('iva_bimestral','Sep-Oct 2026',0,2026,11,25),

        ('iva_bimestral','Nov-Dic 2026', 1,2027,1,13),('iva_bimestral','Nov-Dic 2026', 2,2027,1,14),
        ('iva_bimestral','Nov-Dic 2026', 3,2027,1,15),('iva_bimestral','Nov-Dic 2026', 4,2027,1,18),
        ('iva_bimestral','Nov-Dic 2026', 5,2027,1,19),('iva_bimestral','Nov-Dic 2026', 6,2027,1,20),
        ('iva_bimestral','Nov-Dic 2026', 7,2027,1,21),('iva_bimestral','Nov-Dic 2026', 8,2027,1,22),
        ('iva_bimestral','Nov-Dic 2026', 9,2027,1,25),('iva_bimestral','Nov-Dic 2026', 0,2027,1,26),

        # ── IVA Cuatrimestral ──────────────────────────────────────────
        ('iva_cuatrimestral','Ene-Abr 2026',1,2026,5,12),('iva_cuatrimestral','Ene-Abr 2026',2,2026,5,13),
        ('iva_cuatrimestral','Ene-Abr 2026',3,2026,5,14),('iva_cuatrimestral','Ene-Abr 2026',4,2026,5,15),
        ('iva_cuatrimestral','Ene-Abr 2026',5,2026,5,19),('iva_cuatrimestral','Ene-Abr 2026',6,2026,5,20),
        ('iva_cuatrimestral','Ene-Abr 2026',7,2026,5,21),('iva_cuatrimestral','Ene-Abr 2026',8,2026,5,22),
        ('iva_cuatrimestral','Ene-Abr 2026',9,2026,5,25),('iva_cuatrimestral','Ene-Abr 2026',0,2026,5,26),

        ('iva_cuatrimestral','May-Ago 2026',1,2026,9, 9),('iva_cuatrimestral','May-Ago 2026',2,2026,9,10),
        ('iva_cuatrimestral','May-Ago 2026',3,2026,9,11),('iva_cuatrimestral','May-Ago 2026',4,2026,9,14),
        ('iva_cuatrimestral','May-Ago 2026',5,2026,9,15),('iva_cuatrimestral','May-Ago 2026',6,2026,9,16),
        ('iva_cuatrimestral','May-Ago 2026',7,2026,9,17),('iva_cuatrimestral','May-Ago 2026',8,2026,9,18),
        ('iva_cuatrimestral','May-Ago 2026',9,2026,9,21),('iva_cuatrimestral','May-Ago 2026',0,2026,9,22),

        ('iva_cuatrimestral','Sep-Dic 2026',1,2027,1,13),('iva_cuatrimestral','Sep-Dic 2026',2,2027,1,14),
        ('iva_cuatrimestral','Sep-Dic 2026',3,2027,1,15),('iva_cuatrimestral','Sep-Dic 2026',4,2027,1,18),
        ('iva_cuatrimestral','Sep-Dic 2026',5,2027,1,19),('iva_cuatrimestral','Sep-Dic 2026',6,2027,1,20),
        ('iva_cuatrimestral','Sep-Dic 2026',7,2027,1,21),('iva_cuatrimestral','Sep-Dic 2026',8,2027,1,22),
        ('iva_cuatrimestral','Sep-Dic 2026',9,2027,1,25),('iva_cuatrimestral','Sep-Dic 2026',0,2027,1,26),

        # ── Renta Persona Jurídica ─────────────────────────────────────
        ('renta_juridica','Mayo 2026 (1a cuota)', 1,2026,5,12),('renta_juridica','Mayo 2026 (1a cuota)', 2,2026,5,13),
        ('renta_juridica','Mayo 2026 (1a cuota)', 3,2026,5,14),('renta_juridica','Mayo 2026 (1a cuota)', 4,2026,5,15),
        ('renta_juridica','Mayo 2026 (1a cuota)', 5,2026,5,19),('renta_juridica','Mayo 2026 (1a cuota)', 6,2026,5,20),
        ('renta_juridica','Mayo 2026 (1a cuota)', 7,2026,5,21),('renta_juridica','Mayo 2026 (1a cuota)', 8,2026,5,22),
        ('renta_juridica','Mayo 2026 (1a cuota)', 9,2026,5,25),('renta_juridica','Mayo 2026 (1a cuota)', 0,2026,5,26),

        ('renta_juridica','Julio 2026 (2a cuota)',1,2026,7, 9),('renta_juridica','Julio 2026 (2a cuota)',2,2026,7,10),
        ('renta_juridica','Julio 2026 (2a cuota)',3,2026,7,13),('renta_juridica','Julio 2026 (2a cuota)',4,2026,7,14),
        ('renta_juridica','Julio 2026 (2a cuota)',5,2026,7,15),('renta_juridica','Julio 2026 (2a cuota)',6,2026,7,16),
        ('renta_juridica','Julio 2026 (2a cuota)',7,2026,7,17),('renta_juridica','Julio 2026 (2a cuota)',8,2026,7,21),
        ('renta_juridica','Julio 2026 (2a cuota)',9,2026,7,22),('renta_juridica','Julio 2026 (2a cuota)',0,2026,7,23),
    ]

    for tax_type, period_label, nit_digit, yr, mo, dy in datos:
        db.session.add(TaxDeadline(
            tax_type=tax_type,
            period_label=period_label,
            nit_digit=nit_digit,
            deadline_date=date(yr, mo, dy),
            year=2026,
        ))
    db.session.commit()
    print(f'Calendario tributario 2026 cargado: {len(datos)} plazos.')
