#!/usr/bin/env python
"""
Script de correction automatique des problèmes de sécurité critiques
À exécuter AVANT tout déploiement en production
"""
import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Génère une SECRET_KEY sécurisée"""
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def create_env_file():
    """Crée un fichier .env avec des valeurs sécurisées"""
    if Path('.env').exists():
        print("⚠️  Le fichier .env existe déjà. Création de .env.new")
        env_file = '.env.new'
    else:
        env_file = '.env'
    
    secret_key = generate_secret_key()
    webhook_secret = generate_secret_key()
    
    env_content = f"""# Configuration Sécurisée - Générée automatiquement
# NE PAS COMMITER CE FICHIER

# Django
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DOMAIN=https://votre-domaine.com

# Base de données PostgreSQL
DB_NAME=cahier_charges_db
DB_USER=postgres
DB_PASSWORD=CHANGEZ_MOI
DB_HOST=localhost
DB_PORT=5432

# LigdiCash - REMPLACER PAR VOS VRAIES CLÉS
LIGDICASH_API_KEY=CHANGEZ_MOI
LIGDICASH_AUTH_TOKEN=CHANGEZ_MOI
LIGDICASH_WEBHOOK_SECRET={webhook_secret}
LIGDICASH_TEST_MODE=True

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=CHANGEZ_MOI
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@cahierdecharges.com

# Redis (optionnel)
REDIS_URL=redis://127.0.0.1:6379/1

# Sentry (optionnel)
SENTRY_DSN=
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Fichier {env_file} créé avec succès!")
    print(f"⚠️  IMPORTANT: Modifiez les valeurs CHANGEZ_MOI avant utilisation")
    return True

def update_gitignore():
    """Met à jour le .gitignore pour protéger les fichiers sensibles"""
    gitignore_content = """
# Fichiers sensibles
.env
.env.*
*.log

# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class

# Django
db.sqlite3
media/
staticfiles/
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'a') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore mis à jour")
    return True

def check_requirements():
    """Vérifie et met à jour requirements.txt"""
    required_packages = [
        'Django==5.0.1',
        'reportlab==4.0.9',
        'Pillow==10.1.0',
        'python-dotenv==1.0.0',
        'django-cors-headers==4.3.1',
        'django-ratelimit==4.1.0',
        'psycopg2-binary==2.9.9',
        'gunicorn==21.2.0',
        'whitenoise==6.6.0',
    ]
    
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            current = f.read()
        
        if 'django-ratelimit' not in current:
            print("⚠️  django-ratelimit manquant dans requirements.txt")
            return False
    
    print("✅ requirements.txt vérifié")
    return True

def create_logs_directory():
    """Crée le répertoire logs/"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir()
        (logs_dir / '.gitkeep').touch()
        print("✅ Répertoire logs/ créé")
    return True

def main():
    print("\n" + "="*60)
    print("🔧 SCRIPT DE CORRECTION DES PROBLÈMES DE SÉCURITÉ")
    print("="*60 + "\n")
    
    # Vérifier qu'on est dans le bon répertoire
    if not Path('manage.py').exists():
        print("❌ ERREUR: Ce script doit être exécuté depuis le répertoire Django")
        print("   Répertoire actuel:", os.getcwd())
        return False
    
    print("📁 Répertoire de travail:", os.getcwd())
    print()
    
    # Exécuter les corrections
    tasks = [
        ("Création du fichier .env", create_env_file),
        ("Mise à jour du .gitignore", update_gitignore),
        ("Vérification requirements.txt", check_requirements),
        ("Création répertoire logs/", create_logs_directory),
    ]
    
    results = []
    for task_name, task_func in tasks:
        print(f"\n🔄 {task_name}...")
        try:
            result = task_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    if all(results):
        print("✅ TOUTES LES CORRECTIONS ONT ÉTÉ APPLIQUÉES!")
    else:
        print("⚠️  CERTAINES CORRECTIONS ONT ÉCHOUÉ")
    print("="*60)
    
    print("\n📝 PROCHAINES ÉTAPES MANUELLES:")
    print("1. Modifier le fichier .env avec vos vraies valeurs")
    print("2. Installer les dépendances: pip install -r requirements.txt")
    print("3. Appliquer les corrections dans settings.py, ligdicash_config.py, views_paiement.py")
    print("4. Exécuter: python manage.py check --deploy")
    print("5. Tester l'application en local")
    print("6. NE PAS commiter le fichier .env!")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
