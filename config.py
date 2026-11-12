import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'eventpass-insecure-development-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'eventpass.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail Config (Mock / Local fallback)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@eventpass.edu')
    
    # Upload Directories
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
