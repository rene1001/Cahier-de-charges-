#!/usr/bin/env python
"""
Script simple de vérification de configuration
Sans emojis pour compatibilité Windows
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def test_env_file():
    """Vérifier que .env existe"""
    if not Path('.env').exists():
        print("[FAIL] Fichier .env manquant!")
        print("       -> Executez: copy env.example .env")
        return False
    print("[OK] Fichier .env existe")
    return True

def test_secret_key():
    """Vérifier SECRET_KEY"""
    secret = os.environ.get('SECRET_KEY', '')
    if not secret or 'django-insecure-DEV-ONLY' in secret:
        print("[FAIL] SECRET_KEY non configuree dans .env")
        print("       -> Generer avec: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"")
        return False
    if len(secret) < 50:
        print("[WARN] SECRET_KEY trop courte (< 50 caracteres)")
        return False
    print("[OK] SECRET_KEY configuree")
    return True

def test_ligdicash():
    """Vérifier clés LigdiCash"""
    api_key = os.environ.get('LIGDICASH_API_KEY', '')
    auth_token = os.environ.get('LIGDICASH_AUTH_TOKEN', '')
    webhook = os.environ.get('LIGDICASH_WEBHOOK_SECRET', '')
    
    if not api_key or api_key == 'votre_api_key_ici':
        print("[FAIL] LIGDICASH_API_KEY non configuree")
        return False
    if not auth_token or auth_token == 'votre_auth_token_ici':
        print("[FAIL] LIGDICASH_AUTH_TOKEN non configuree")
        return False
    if not webhook or webhook == 'generer-un-secret-aleatoire-ici':
        print("[FAIL] LIGDICASH_WEBHOOK_SECRET non configuree")
        print("       -> Generer avec: python -c \"import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(64)))\"")
        return False
    print("[OK] Cles LigdiCash configurees")
    return True

def test_code_changes():
    """Vérifier que les corrections sont appliquées"""
    settings = Path('django_project/settings.py')
    if not settings.exists():
        print("[FAIL] settings.py introuvable")
        return False
    
    content = settings.read_text()
    
    # Vérifier SECRET_KEY
    if "os.environ.get('SECRET_KEY'" not in content:
        print("[FAIL] settings.py: SECRET_KEY non corrigee")
        return False
    
    # Vérifier CORS
    if "CORS_ALLOW_ALL_ORIGINS = True" in content:
        print("[FAIL] settings.py: CORS_ALLOW_ALL_ORIGINS encore a True")
        return False
    
    # Vérifier X_FRAME_OPTIONS
    if "X_FRAME_OPTIONS = 'ALLOWALL'" in content:
        print("[FAIL] settings.py: X_FRAME_OPTIONS encore a ALLOWALL")
        return False
    
    # Vérifier CSRF
    if "CSRF_COOKIE_HTTPONLY = False" in content:
        print("[FAIL] settings.py: CSRF_COOKIE_HTTPONLY encore a False")
        return False
    
    print("[OK] Corrections appliquees dans settings.py")
    return True

def test_webhook():
    """Vérifier webhook sécurisé"""
    views = Path('cahier_charges/views_paiement.py')
    if not views.exists():
        print("[WARN] views_paiement.py introuvable")
        return True
    
    content = views.read_text()
    if 'verify_ligdicash_signature' not in content:
        print("[FAIL] Verification signature webhook manquante")
        return False
    
    print("[OK] Webhook securise")
    return True

def main():
    print("="*60)
    print("VERIFICATION DE CONFIGURATION")
    print("="*60)
    
    tests = [
        ("Fichier .env", test_env_file),
        ("SECRET_KEY", test_secret_key),
        ("Cles LigdiCash", test_ligdicash),
        ("Corrections code", test_code_changes),
        ("Webhook securise", test_webhook),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\nTest: {name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[ERROR] {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTATS: {passed} OK, {failed} FAIL")
    print("="*60)
    
    if failed == 0:
        print("\nFELICITATIONS! Configuration complete!")
        print("Vous pouvez executer: python manage.py runserver")
        return True
    else:
        print(f"\nATTENTION: {failed} probleme(s) detecte(s)")
        print("Consultez les messages ci-dessus pour corriger")
        return False

if __name__ == '__main__':
    # Vérifier qu'on est dans le bon répertoire
    if not Path('manage.py').exists():
        print("[ERROR] Ce script doit etre execute depuis le repertoire Django")
        print(f"        Repertoire actuel: {os.getcwd()}")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)
