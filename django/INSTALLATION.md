# 🚀 GUIDE D'INSTALLATION - APPLICATION SÉCURISÉE

## ✅ Corrections Appliquées

Les **8 problèmes critiques** ont été corrigés dans le code source.

---

## 📋 ÉTAPES D'INSTALLATION

### 1️⃣ Créer le fichier .env

```powershell
# Dans le répertoire du projet
cd c:\wamp64\www\django\django

# Copier le template
copy env.example .env
```

### 2️⃣ Générer les secrets

**Générer SECRET_KEY:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Générer WEBHOOK_SECRET:**
```powershell
python -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for _ in range(64)))"
```

### 3️⃣ Éditer le fichier .env

Ouvrir `.env` et configurer:

```env
# Coller la SECRET_KEY générée
SECRET_KEY=votre_secret_key_generee_ici

# Mode développement
DEBUG=True
DOMAIN=http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1

# LigdiCash - Vos vraies clés
LIGDICASH_API_KEY=votre_api_key_ligdicash
LIGDICASH_AUTH_TOKEN=votre_auth_token_ligdicash
LIGDICASH_WEBHOOK_SECRET=votre_webhook_secret_genere
LIGDICASH_TEST_MODE=True

# Base de données (laisser vide pour SQLite en dev)
DB_PASSWORD=
```

### 4️⃣ Installer les dépendances

```powershell
pip install -r requirements.txt
```

### 5️⃣ Vérifier la configuration

```powershell
python manage.py check
```

**Résultat attendu:** ✅ `System check identified no issues (0 silenced).`

### 6️⃣ Migrer la base de données

```powershell
python manage.py migrate
```

### 7️⃣ Lancer le serveur

```powershell
python manage.py runserver
```

**Accéder à:** http://localhost:8000

---

## 🔒 Configuration Production

### Fichier .env pour Production

```env
# Django
SECRET_KEY=<votre_secret_key_production>
DEBUG=False
DOMAIN=https://votre-domaine.com
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# PostgreSQL
DB_ENGINE=postgresql
DB_NAME=cahier_charges_db
DB_USER=postgres
DB_PASSWORD=mot_de_passe_fort_postgresql
DB_HOST=localhost
DB_PORT=5432

# LigdiCash Production
LIGDICASH_API_KEY=votre_vraie_cle_production
LIGDICASH_AUTH_TOKEN=votre_vrai_token_production
LIGDICASH_WEBHOOK_SECRET=<votre_webhook_secret_fort>
LIGDICASH_TEST_MODE=False

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=mot_de_passe_app_gmail
EMAIL_USE_TLS=True
```

### Installer PostgreSQL

```powershell
# Télécharger et installer PostgreSQL
# https://www.postgresql.org/download/windows/

# Créer la base de données
createdb cahier_charges_db
```

### Vérification finale

```powershell
python manage.py check --deploy
```

**6 avertissements sont normaux** tant que DEBUG=True. Avec DEBUG=False et HTTPS, ils disparaîtront.

---

## ✅ Checklist de Vérification

- [ ] Fichier `.env` créé et configuré
- [ ] SECRET_KEY générée (50+ caractères)
- [ ] WEBHOOK_SECRET généré (64+ caractères)
- [ ] Clés LigdiCash configurées
- [ ] `pip install -r requirements.txt` exécuté
- [ ] `python manage.py check` passe sans erreur
- [ ] `python manage.py migrate` exécuté
- [ ] Serveur démarre sans erreur
- [ ] `.env` n'est PAS commité dans git

---

## 🎯 Résumé des Corrections

| Problème | Status |
|----------|--------|
| 1. SECRET_KEY exposée | ✅ Corrigé |
| 2. API Keys hardcodées | ✅ Corrigé |
| 3. DEBUG = True | ✅ Corrigé |
| 4. CORS_ALLOW_ALL_ORIGINS | ✅ Corrigé |
| 5. X_FRAME_OPTIONS | ✅ Corrigé |
| 6. CSRF_COOKIE_HTTPONLY | ✅ Corrigé |
| 7. SQLite en production | ✅ Corrigé |
| 8. Webhook sans signature | ✅ Corrigé |

---

## 📄 Fichiers Modifiés

### Code Source
- `django_project/settings.py` - Configuration sécurisée
- `cahier_charges/ligdicash_config.py` - Clés depuis .env
- `cahier_charges/views_paiement.py` - Vérification signature webhook
- `requirements.txt` - Dépendances ajoutées

### Nouveaux Fichiers
- `env.example` - Template de configuration
- `logs/` - Répertoire pour logs
- `CORRECTIONS_APPLIQUEES.md` - Détails des corrections
- `INSTALLATION.md` - Ce fichier

---

## 🆘 Dépannage

### Erreur: "SECRET_KEY not found"
→ Créez le fichier `.env` et ajoutez une SECRET_KEY

### Erreur: "No module named 'dotenv'"
```powershell
pip install python-dotenv
```

### Erreur: "No module named 'corsheaders'"
```powershell
pip install django-cors-headers
```

### Avertissement: "Using default SECRET_KEY"
→ Configurez SECRET_KEY dans le fichier `.env`

---

## 📞 Support

**Fichiers de référence:**
- `RAPPORT_TEST_SECURITE.md` - Audit complet
- `CORRECTIONS_APPLIQUEES.md` - Détails des corrections
- `README_TESTS.md` - Résumé des tests

**Scripts utiles:**
- `test_securite.py` - Tests automatisés
- `CORRECTIFS_URGENTS.py` - Script de configuration

---

## ⚠️ IMPORTANT

**NE JAMAIS COMMITER LE FICHIER .env!**

Le fichier `.env` est déjà dans `.gitignore`.

Seul `env.example` doit être versionné dans git.

---

**Votre application est maintenant sécurisée! 🎉**
