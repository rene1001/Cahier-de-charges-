# Guide d'intégration LigdiCash

Ce guide explique comment utiliser l'intégration LigdiCash pour accepter des paiements dans votre application Django.

## 📋 Sommaire

1. [Présentation de LigdiCash](#présentation)
2. [Configuration initiale](#configuration)
3. [Obtenir les clés API](#obtenir-les-clés-api)
4. [Test de l'intégration](#test-de-lintégration)
5. [Mise en production](#mise-en-production)
6. [Dépannage](#dépannage)

---

## 🎯 Présentation

**LigdiCash** est une solution de paiement mobile très populaire en Afrique de l'Ouest, permettant :

- ✅ Paiements Mobile Money (MTN, Moov, Orange, Wave)
- ✅ Paiements par carte bancaire (Visa, Mastercard)
- ✅ Transactions en XOF (Franc CFA)
- ✅ API REST simple et sécurisée
- ✅ Webhooks pour les notifications temps réel

---

## ⚙️ Configuration

### 1. Obtenir les clés API

1. Créez un compte sur [https://ligdicash.com](https://ligdicash.com)
2. Accédez au tableau de bord développeur
3. Récupérez :
   - **API Key** (clé publique) : `pk_test_...` (test) ou `pk_live_...` (production)
   - **Auth Token** (clé privée) : `auth_test_...` (test) ou `auth_live_...` (production)

### 2. Configuration de l'application

#### Fichier `cahier_charges/ligdicash_config.py`

Modifiez les valeurs suivantes :

```python
LIGDICASH_CONFIG = {
    'API_KEY': 'votre_api_key_ici',  # Clé API de LigdiCash
    'AUTH_TOKEN': 'votre_auth_token_ici',  # Token d'authentification
    'API_URL': 'https://app.ligdicash.com/pay/v01/straight/sdk/',
    'VERIFY_URL': 'https://app.ligdicash.com/pay/v01/straight/check_payment/',
    'NOTIFY_URL': 'http://localhost:8000/paiement/ligdicash/notify/',
    'RETURN_URL': 'http://localhost:8000/paiement/ligdicash/retour/',
    'CANCEL_URL': 'http://localhost:8000/paiement/ligdicash/annulation/',
    'CURRENCY': 'XOF',  # Franc CFA
    'LANG': 'fr',
    'TEST_MODE': True,  # False en production
}
```

#### Fichier `.env` (optionnel)

Vous pouvez aussi utiliser des variables d'environnement :

```bash
LIGDICASH_API_KEY=pk_test_votre_cle
LIGDICASH_AUTH_TOKEN=auth_test_votre_token
LIGDICASH_TEST_MODE=True
```

---

## 🧪 Test de l'intégration

### 1. Vérifier la configuration

```bash
python manage.py check
```

### 2. Lancer le serveur de développement

```bash
python manage.py runserver
```

### 3. Tester un paiement

1. Accédez à : http://localhost:8000/abonnement/
2. Sélectionnez un plan payant
3. Cliquez sur **"Payer avec LigdiCash"**
4. Vous serez redirigé vers la page de paiement LigdiCash

### 4. Numéros de test

En mode test, utilisez ces numéros :

- **MTN Mobile Money** : `22997000001` (succès) / `22997000002` (échec)
- **Moov Money** : `22996000001` (succès) / `22996000002` (échec)
- **Carte bancaire** : Utilisez les cartes de test fournies par LigdiCash

---

## 🚀 Mise en production

### 1. Obtenir les clés de production

Sur votre tableau de bord LigdiCash, passez en mode production et récupérez :
- **API Key de production** : `pk_live_...`
- **Auth Token de production** : `auth_live_...`

### 2. Modifier la configuration

Dans `ligdicash_config.py` :

```python
LIGDICASH_CONFIG = {
    'API_KEY': 'pk_live_votre_cle_production',
    'AUTH_TOKEN': 'auth_live_votre_token_production',
    'TEST_MODE': False,  # ⚠️ IMPORTANT : désactiver le mode test
    # ... autres paramètres
}
```

### 3. Mettre à jour les URLs de callback

Remplacez `localhost` par votre domaine de production :

```python
'NOTIFY_URL': 'https://votredomaine.com/paiement/ligdicash/notify/',
'RETURN_URL': 'https://votredomaine.com/paiement/ligdicash/retour/',
'CANCEL_URL': 'https://votredomaine.com/paiement/ligdicash/annulation/',
```

### 4. Configurer les webhooks sur LigdiCash

Dans votre tableau de bord LigdiCash :
1. Allez dans **Paramètres > Webhooks**
2. Ajoutez l'URL : `https://votredomaine.com/paiement/ligdicash/notify/`
3. Activez les notifications pour : `payment.success`, `payment.failed`

### 5. Sécurité en production

Dans `settings.py`, assurez-vous que :

```python
DEBUG = False
ALLOWED_HOSTS = ['votredomaine.com', 'www.votredomaine.com', 'app.ligdicash.com']
CSRF_TRUSTED_ORIGINS = ['https://votredomaine.com', 'https://app.ligdicash.com']
```

---

## 🔧 Architecture de l'intégration

### Fichiers principaux

- **`ligdicash_config.py`** : Configuration LigdiCash
- **`ligdicash_client.py`** : Client API pour communiquer avec LigdiCash
- **`models_paiement.py`** : Modèle `TransactionLigdiCash` pour stocker les transactions
- **`views_paiement.py`** : Vues pour gérer les paiements
- **`urls.py`** : Routes pour les paiements

### Flux de paiement

1. **Utilisateur** clique sur "Payer avec LigdiCash"
2. **Django** crée une transaction en base de données (statut: `pending`)
3. **Django** appelle l'API LigdiCash pour initialiser le paiement
4. **LigdiCash** renvoie une URL de paiement
5. **Utilisateur** est redirigé vers LigdiCash et effectue le paiement
6. **LigdiCash** envoie une notification webhook à Django (notification)
7. **Django** vérifie le paiement et met à jour la transaction (statut: `successful`)
8. **Django** crée/prolonge l'abonnement de l'utilisateur
9. **Utilisateur** est redirigé vers la page de confirmation

---

## 🐛 Dépannage

### Erreur : "URL de paiement manquante"

**Cause** : L'API LigdiCash n'a pas renvoyé d'URL de paiement

**Solution** :
1. Vérifiez vos clés API dans `ligdicash_config.py`
2. Vérifiez que vous êtes en mode test avec des clés de test
3. Consultez les logs Django : `logs/django.log`

### Erreur : "Erreur HTTP 401"

**Cause** : Clés API invalides ou expirées

**Solution** :
1. Vérifiez que votre API Key et Auth Token sont corrects
2. Assurez-vous d'utiliser les bonnes clés (test ou production)
3. Reconnectez-vous à votre compte LigdiCash

### Le webhook ne fonctionne pas

**Cause** : LigdiCash ne peut pas joindre votre serveur

**Solution** :
1. En développement local, utilisez [ngrok](https://ngrok.com/) pour exposer votre serveur :
   ```bash
   ngrok http 8000
   ```
2. Mettez à jour `NOTIFY_URL` avec l'URL ngrok
3. En production, vérifiez que votre serveur est accessible publiquement

### Paiement en attente indéfiniment

**Cause** : La notification webhook n'est pas reçue

**Solution** :
1. Vérifiez la configuration webhook sur LigdiCash
2. Consultez les logs de votre serveur web
3. Testez manuellement la vérification :
   ```python
   from cahier_charges.ligdicash_client import LigdiCashClient
   client = LigdiCashClient()
   result = client.verifier_paiement('token_de_paiement')
   print(result)
   ```

---

## 📊 Administration

Les transactions sont visibles dans l'interface d'administration Django :

1. Accédez à : http://localhost:8000/admin/
2. Allez dans **Cahier Charges > Transactions LigdiCash**
3. Vous pouvez voir toutes les transactions avec leurs statuts

---

## 📞 Support

- **Documentation LigdiCash** : https://developers.ligdicash.com/
- **Support LigdiCash** : support@ligdicash.com
- **Communauté LigdiCash** : [Forum développeurs](https://community.ligdicash.com/)

---

## ✅ Checklist de mise en production

- [ ] Clés API de production configurées
- [ ] `TEST_MODE = False` dans la configuration
- [ ] URLs de callback mises à jour avec le domaine de production
- [ ] Webhooks configurés sur le tableau de bord LigdiCash
- [ ] `DEBUG = False` dans settings.py
- [ ] HTTPS activé sur votre serveur
- [ ] Paiement test effectué avec succès
- [ ] Logs vérifiés et sans erreurs

---

**Dernière mise à jour** : 19 octobre 2025
