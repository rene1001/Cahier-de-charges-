"""
Configuration LigdiCash pour les paiements - SÉCURISÉE
Documentation: https://developers.ligdicash.com/
"""
import os
from dotenv import load_dotenv

load_dotenv()

# CORRECTION: Clés API depuis variables d'environnement (problème critique #2)
# Configuration LigdiCash SÉCURISÉE
LIGDICASH_CONFIG = {
    'API_KEY': os.environ.get('LIGDICASH_API_KEY', 'pk_test_default'),
    'AUTH_TOKEN': os.environ.get('LIGDICASH_AUTH_TOKEN', 'auth_test_default'),
    'WEBHOOK_SECRET': os.environ.get('LIGDICASH_WEBHOOK_SECRET', 'change_me_in_production'),
    'API_URL': 'https://app.ligdicash.com/pay/v01/straight/sdk/',
    'VERIFY_URL': 'https://app.ligdicash.com/pay/v01/straight/check_payment/',
    'NOTIFY_URL': f"{os.environ.get('DOMAIN', 'http://localhost:8000')}/paiement/ligdicash/notify/",
    'RETURN_URL': f"{os.environ.get('DOMAIN', 'http://localhost:8000')}/paiement/ligdicash/retour/",
    'CANCEL_URL': f"{os.environ.get('DOMAIN', 'http://localhost:8000')}/paiement/ligdicash/annulation/",
    'CURRENCY': 'XOF',  # Devise par défaut (XOF pour le Franc CFA)
    'LANG': 'fr',
    'TEST_MODE': os.environ.get('LIGDICASH_TEST_MODE', 'True') == 'True',
    'DESCRIPTION': 'Abonnement Cahier de Charges',
    'CUSTOMER': 'Cahier de Charges App',
}

# Vérification des clés en production
if not LIGDICASH_CONFIG['TEST_MODE']:
    import warnings
    if LIGDICASH_CONFIG['API_KEY'] == 'pk_test_default' or LIGDICASH_CONFIG['AUTH_TOKEN'] == 'auth_test_default':
        warnings.warn("WARNING: Using default LigdiCash keys in production! Set LIGDICASH_API_KEY and LIGDICASH_AUTH_TOKEN in .env")
    if LIGDICASH_CONFIG['WEBHOOK_SECRET'] == 'change_me_in_production':
        warnings.warn("CRITICAL: Set LIGDICASH_WEBHOOK_SECRET in .env for production!")
