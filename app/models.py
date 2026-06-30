from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from flask import current_app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # admin, editor, viewer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_label(self):
        labels = {'admin': 'Administrador', 'editor': 'Editor', 'viewer': 'Visualizador'}
        return labels.get(self.role, self.role)

    @property
    def role_color(self):
        colors = {'admin': 'danger', 'editor': 'primary', 'viewer': 'secondary'}
        return colors.get(self.role, 'secondary')


class Entity(db.Model):
    __tablename__ = 'entities'

    id = db.Column(db.Integer, primary_key=True)
    cedula_nit = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    entity_type = db.Column(db.String(20), nullable=False, default='persona')  # persona, empresa
    place = db.Column(db.String(100))  # Lugar / municipio de la empresa
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    credentials = db.relationship('Credential', back_populates='entity',
                                  cascade='all, delete-orphan', order_by='Credential.id')


class Site(db.Model):
    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.String(500), default='')
    category = db.Column(db.String(50), default='otro')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    credentials = db.relationship('Credential', back_populates='site')

    CATEGORIES = {
        'impuestos': 'Impuestos y Tributario',
        'aportes':   'Aportes y Nómina',
        'correo':    'Correos',
        'camara':    'Cámara de Comercio',
        'banco':     'Bancos',
        'otro':      'Otros',
    }

    @property
    def category_label(self):
        return self.CATEGORIES.get(self.category, 'Otros')


class Credential(db.Model):
    __tablename__ = 'credentials'

    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entities.id'), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    username = db.Column(db.String(200), default='')
    alt_username = db.Column(db.String(200), default='')
    encrypted_password = db.Column(db.Text, default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    entity = db.relationship('Entity', back_populates='credentials')
    site = db.relationship('Site', back_populates='credentials')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def set_password(self, plain_password):
        if not plain_password:
            self.encrypted_password = ''
            return
        key = current_app.config['ENCRYPTION_KEY'].encode()
        f = Fernet(key)
        self.encrypted_password = f.encrypt(plain_password.encode()).decode()

    def get_password(self):
        if not self.encrypted_password:
            return ''
        key = current_app.config['ENCRYPTION_KEY'].encode()
        f = Fernet(key)
        return f.decrypt(self.encrypted_password.encode()).decode()

    @property
    def last_modified_by(self):
        if self.updated_by:
            return self.updated_by.username
        if self.created_by:
            return self.created_by.username
        return '—'

    @property
    def last_modified_at(self):
        return self.updated_at or self.created_at


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50))
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    ACTION_ICONS = {
        'create': ('success', 'plus-circle'),
        'update': ('warning', 'edit'),
        'delete': ('danger', 'trash'),
        'view':   ('info', 'eye'),
    }

    @property
    def action_color(self):
        return self.ACTION_ICONS.get(self.action, ('secondary', 'circle'))[0]

    @property
    def action_icon(self):
        return self.ACTION_ICONS.get(self.action, ('secondary', 'circle'))[1]


def get_nit_last_digit(cedula_nit):
    nit = cedula_nit.strip().replace(' ', '').replace('.', '')
    if '-' in nit:
        nit = nit.split('-')[0]
    digits = ''.join(c for c in nit if c.isdigit())
    return int(digits[-1]) if digits else None


class TaxDeadline(db.Model):
    __tablename__ = 'tax_deadlines'

    id = db.Column(db.Integer, primary_key=True)
    tax_type = db.Column(db.String(50), nullable=False)
    period_label = db.Column(db.String(100), nullable=False)
    nit_digit = db.Column(db.Integer, nullable=False)
    deadline_date = db.Column(db.Date, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    TAX_TYPES = {
        'retefuente':       ('Retención en la Fuente', 'warning',  'fa-percentage'),
        'iva_bimestral':    ('IVA Bimestral',          'primary',  'fa-receipt'),
        'iva_cuatrimestral':('IVA Cuatrimestral',      'info',     'fa-file-invoice'),
        'renta_juridica':   ('Renta Persona Jurídica', 'danger',   'fa-building'),
    }

    @property
    def tax_label(self):
        return self.TAX_TYPES.get(self.tax_type, (self.tax_type, 'secondary', 'fa-file'))[0]

    @property
    def tax_color(self):
        return self.TAX_TYPES.get(self.tax_type, (self.tax_type, 'secondary', 'fa-file'))[1]

    @property
    def tax_icon(self):
        return self.TAX_TYPES.get(self.tax_type, (self.tax_type, 'secondary', 'fa-file'))[2]
