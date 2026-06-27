import os
from sqlalchemy.pool import NullPool

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///passwords.db')
    # Render entrega postgres://, SQLAlchemy necesita postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Evita que los workers de gunicorn hereden conexiones SSL corruptas
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'poolclass': NullPool,
    }

    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7200  # 2 horas
