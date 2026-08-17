import os
import sys

# Détecter l'environnement
if 'RENDER' in os.environ:
    # En production sur Render
    DATABASE_URL = os.environ.get('DATABASE_URL')
else:
    # En développement local
    DATABASE_URL = 'sqlite:///phenix.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
