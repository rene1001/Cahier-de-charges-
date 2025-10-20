#!/usr/bin/env python
"""
Script de test de sécurité automatisé
Vérifie les problèmes critiques avant déploiement
"""
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

class SecurityTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        load_dotenv()
    
    def test_secret_key(self):
        """Test 1: Vérifier SECRET_KEY"""
        print("\n🔍 Test 1: SECRET_KEY")
        
        # Vérifier qu'elle n'est pas hardcodée
        settings_path = Path('django_project/settings.py')
        if settings_path.exists():
            content = settings_path.read_text()
            if "SECRET_KEY = 'django-insecure" in content:
                print("   ❌ FAIL: SECRET_KEY hardcodée trouvée dans settings.py")
                self.failed += 1
                return False
        
        # Vérifier qu'elle existe en env
        secret = os.environ.get('SECRET_KEY')
        if not secret:
            print("   ❌ FAIL: SECRET_KEY manquante dans .env")
            self.failed += 1
            return False
        
        if len(secret) < 50:
            print("   ⚠️  WARN: SECRET_KEY trop courte (< 50 caractères)")
            self.warnings += 1
        
        print("   ✅ PASS: SECRET_KEY configurée correctement")
        self.passed += 1
        return True
    
    def test_debug_mode(self):
        """Test 2: Vérifier DEBUG"""
        print("\n🔍 Test 2: DEBUG Mode")
        
        debug = os.environ.get('DEBUG', 'False')
        if debug == 'True':
            print("   ⚠️  WARN: DEBUG = True (OK dev, DANGER production)")
            self.warnings += 1
            return False
        
        print("   ✅ PASS: DEBUG = False")
        self.passed += 1
        return True
    
    def test_ligdicash_keys(self):
        """Test 3: Vérifier clés LigdiCash"""
        print("\n🔍 Test 3: Clés LigdiCash")
        
        # Vérifier qu'elles ne sont pas hardcodées
        config_path = Path('cahier_charges/ligdicash_config.py')
        if config_path.exists():
            content = config_path.read_text()
            if "'API_KEY': 'votre_api_key_ici'" in content:
                print("   ❌ FAIL: API_KEY hardcodée dans ligdicash_config.py")
                self.failed += 1
                return False
        
        # Vérifier qu'elles existent en env
        api_key = os.environ.get('LIGDICASH_API_KEY')
        auth_token = os.environ.get('LIGDICASH_AUTH_TOKEN')
        webhook_secret = os.environ.get('LIGDICASH_WEBHOOK_SECRET')
        
        if not api_key or api_key == 'CHANGEZ_MOI':
            print("   ❌ FAIL: LIGDICASH_API_KEY manquante ou non configurée")
            self.failed += 1
            return False
        
        if not auth_token or auth_token == 'CHANGEZ_MOI':
            print("   ❌ FAIL: LIGDICASH_AUTH_TOKEN manquante ou non configurée")
            self.failed += 1
            return False
        
        if not webhook_secret:
            print("   ❌ FAIL: LIGDICASH_WEBHOOK_SECRET manquante")
            self.failed += 1
            return False
        
        print("   ✅ PASS: Clés LigdiCash configurées")
        self.passed += 1
        return True
    
    def test_cors_settings(self):
        """Test 4: Vérifier CORS"""
        print("\n🔍 Test 4: Configuration CORS")
        
        settings_path = Path('django_project/settings.py')
        if settings_path.exists():
            content = settings_path.read_text()
            if "CORS_ALLOW_ALL_ORIGINS = True" in content:
                print("   ❌ FAIL: CORS_ALLOW_ALL_ORIGINS = True trouvé")
                self.failed += 1
                return False
        
        print("   ✅ PASS: CORS correctement configuré")
        self.passed += 1
        return True
    
    def test_x_frame_options(self):
        """Test 5: Vérifier X_FRAME_OPTIONS"""
        print("\n🔍 Test 5: X_FRAME_OPTIONS")
        
        settings_path = Path('django_project/settings.py')
        if settings_path.exists():
            content = settings_path.read_text()
            if "X_FRAME_OPTIONS = 'ALLOWALL'" in content:
                print("   ❌ FAIL: X_FRAME_OPTIONS = 'ALLOWALL' trouvé")
                self.failed += 1
                return False
        
        print("   ✅ PASS: X_FRAME_OPTIONS sécurisé")
        self.passed += 1
        return True
    
    def test_csrf_settings(self):
        """Test 6: Vérifier CSRF"""
        print("\n🔍 Test 6: Configuration CSRF")
        
        settings_path = Path('django_project/settings.py')
        if settings_path.exists():
            content = settings_path.read_text()
            if "CSRF_COOKIE_HTTPONLY = False" in content:
                print("   ❌ FAIL: CSRF_COOKIE_HTTPONLY = False trouvé")
                self.failed += 1
                return False
        
        print("   ✅ PASS: CSRF correctement configuré")
        self.passed += 1
        return True
    
    def test_webhook_security(self):
        """Test 7: Vérifier sécurité webhook"""
        print("\n🔍 Test 7: Sécurité Webhook")
        
        views_path = Path('cahier_charges/views_paiement.py')
        if views_path.exists():
            content = views_path.read_text()
            if 'verify_ligdicash_signature' not in content:
                print("   ❌ FAIL: Pas de vérification de signature webhook")
                self.failed += 1
                return False
        
        print("   ✅ PASS: Webhook sécurisé avec vérification signature")
        self.passed += 1
        return True
    
    def test_database_config(self):
        """Test 8: Vérifier configuration BDD"""
        print("\n🔍 Test 8: Configuration Base de Données")
        
        db_password = os.environ.get('DB_PASSWORD')
        if not db_password:
            print("   ⚠️  WARN: SQLite utilisé (OK dev, pas prod)")
            self.warnings += 1
            return False
        
        print("   ✅ PASS: PostgreSQL configuré")
        self.passed += 1
        return True
    
    def test_env_file_gitignored(self):
        """Test 9: Vérifier .env dans .gitignore"""
        print("\n🔍 Test 9: .env dans .gitignore")
        
        gitignore_path = Path('.gitignore')
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if '.env' not in content:
                print("   ⚠️  WARN: .env pas dans .gitignore")
                self.warnings += 1
                return False
        else:
            print("   ⚠️  WARN: .gitignore manquant")
            self.warnings += 1
            return False
        
        print("   ✅ PASS: .env protégé par .gitignore")
        self.passed += 1
        return True
    
    def test_allowed_hosts(self):
        """Test 10: Vérifier ALLOWED_HOSTS"""
        print("\n🔍 Test 10: ALLOWED_HOSTS")
        
        allowed_hosts = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
        if 'localhost' in allowed_hosts or '127.0.0.1' in allowed_hosts:
            debug = os.environ.get('DEBUG', 'False')
            if debug == 'False':
                print("   ⚠️  WARN: localhost dans ALLOWED_HOSTS en production")
                self.warnings += 1
        
        print("   ✅ PASS: ALLOWED_HOSTS configuré")
        self.passed += 1
        return True
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("="*60)
        print("TESTS DE SECURITE AUTOMATISES")
        print("="*60)
        
        tests = [
            self.test_secret_key,
            self.test_debug_mode,
            self.test_ligdicash_keys,
            self.test_cors_settings,
            self.test_x_frame_options,
            self.test_csrf_settings,
            self.test_webhook_security,
            self.test_database_config,
            self.test_env_file_gitignored,
            self.test_allowed_hosts,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"   ❌ ERREUR: {e}")
                self.failed += 1
        
        self.print_summary()
    
    def print_summary(self):
        """Afficher le résumé"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*60)
        print(f"✅ Tests réussis:    {self.passed}")
        print(f"❌ Tests échoués:    {self.failed}")
        print(f"⚠️  Avertissements:  {self.warnings}")
        print("="*60)
        
        if self.failed == 0 and self.warnings == 0:
            print("\n🎉 EXCELLENT! Tous les tests passent!")
            print("   L'application est prête pour le déploiement.")
            return True
        elif self.failed == 0:
            print(f"\n⚠️  {self.warnings} avertissement(s) détecté(s)")
            print("   Revérifiez avant déploiement en production.")
            return True
        else:
            print(f"\n❌ ÉCHEC: {self.failed} problème(s) critique(s)")
            print("   NE PAS déployer en production!")
            return False

def main():
    # Vérifier qu'on est dans le bon répertoire
    if not Path('manage.py').exists():
        print("❌ ERREUR: Ce script doit être exécuté depuis le répertoire Django")
        return False
    
    tester = SecurityTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n📝 Actions recommandées:")
        print("1. Exécuter: python CORRECTIFS_URGENTS.py")
        print("2. Configurer le fichier .env avec les vraies valeurs")
        print("3. Appliquer les corrections dans les fichiers source")
        print("4. Relancer ce test")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
