"""
Point d'entrée de l'application
Commande : python run.py
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # ⚠️ IMPORTANT : Utiliser le port donné par Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
