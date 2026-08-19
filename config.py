import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # ============================================================
    # BASE DE DONNÉES - SQLite (Pas besoin de PostgreSQL)
    # ============================================================
    SQLALCHEMY_DATABASE_URI = 'sqlite:///phenix.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail (optionnel pour l'instant)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Upload
    UPLOAD_FOLDER = 'uploads/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Pointage - Coordonnées de l'entreprise
    ENTREPRISE_LAT = 6.3600
    ENTREPRISE_LNG = 2.4150
    RAYON_POINTAGE = 0.005

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False