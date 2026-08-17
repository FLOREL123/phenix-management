"""
Initialisation de l'application Flask
"""
from flask import Flask
import os
from dotenv import load_dotenv

# Importer les extensions depuis extensions.py
from app.extensions import db, login_manager, mail

# Charger les variables d'environnement
load_dotenv()

def create_app():
    """Fonction de création de l'application Flask"""
    
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    
    # ============================================================
    # CONFIGURATION DE L'APPLICATION
    # ============================================================
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ma_cle_secrete_123456')
    
    # Gestion de la base de données (SQLite pour local, PostgreSQL pour Render)
    if 'RENDER' in os.environ:
        # En production sur Render
        DATABASE_URL = os.environ.get('DATABASE_URL')
    else:
        # En développement local (SQLite)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'phenix.db')
        DATABASE_URL = f'sqlite:///{db_path}'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuration des emails
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Configuration des fichiers uploadés
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Coordonnées de l'entreprise pour la géolocalisation
    app.config['ENTREPRISE_LAT'] = 6.3600
    app.config['ENTREPRISE_LNG'] = 2.4150
    app.config['RAYON_POINTAGE'] = 0.005
    
    # ============================================================
    # INITIALISER LES EXTENSIONS AVEC L'APPLICATION
    # ============================================================
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configuration de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    # ============================================================
    # IMPORTER ET ENREGISTRER LES BLUEPRINTS
    # ============================================================
    from app.auth import auth_bp
    from app.routes import routes_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    
    # ============================================================
    # RETOURNER L'APPLICATION
    # ============================================================
    return app
