import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Ensure required static directories exist
    static_dirs = [
        os.path.join(app.root_path, 'static', 'qrcodes'),
        os.path.join(app.root_path, 'static', 'certs'),
        os.path.join(app.root_path, 'static', 'banners'),
        os.path.join(app.root_path, 'static', 'templates')
    ]
    for d in static_dirs:
        os.makedirs(d, exist_ok=True)

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.events.routes import events_bp
    from app.registrations.routes import reg_bp
    from app.certificates.routes import certs_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(reg_bp, url_prefix='/registrations')
    app.register_blueprint(certs_bp, url_prefix='/certificates')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Home route redirect
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('events.list_events'))

    return app
