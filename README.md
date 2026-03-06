# CamionSuf — Backend Flask (WhatsApp Cloud API)

Backend Python Flask qui envoie des notifications WhatsApp automatiques à chaque
étape clé de la livraison (25 %, 50 %, 75 %, 100 %).

## Structure

```
backend/
├── app.py                 # Point d'entrée Flask
├── requirements.txt
├── .env.example           # Variables à copier dans .env
├── routes/
│   └── tracking.py        # POST /track
└── services/
    └── whatsapp.py        # Envoi via Meta Cloud API
```

## Prérequis

- Python 3.10+
- Un compte Meta for Developers avec une app WhatsApp Business configurée
  → https://developers.facebook.com/apps/

## Installation locale

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
# Remplissez .env avec vos tokens Meta
python app.py
```

## Variables d'environnement

| Variable | Description |
|---|---|
| `WHATSAPP_ACCESS_TOKEN` | Token d'accès Meta (permanent ou temporaire) |
| `WHATSAPP_PHONE_NUMBER_ID` | ID du numéro WhatsApp Business |
| `TRACKING_SECRET` | Clé secrète partagée avec Vercel (`api/notify.js`) |
| `FRONTEND_URL` | URL du frontend (ex: https://camionsuf.vercel.app) |

## Endpoint

### `POST /track`

**Corps JSON :**
```json
{
  "secret":  "votre-secret",
  "phone":   "221771234567",
  "message": "🚚 Votre livraison est à 50% !",
  "url":     "https://camionsuf.vercel.app/suivi?cmd=CMD-1234567890"
}
```

**Réponse :**
```json
{
  "success": true,
  "phone": "221771234567",
  "preview": "🚚 Votre livraison est à 50% !…",
  "meta": { ... }
}
```

## Déploiement sur Render

1. Créer un nouveau **Web Service** sur https://render.com
2. Connecter ce dépôt (ou le dossier `backend/`)
3. Build command : `pip install -r requirements.txt`
4. Start command : `gunicorn app:app`
5. Ajouter les variables d'environnement dans l'onglet *Environment*
6. Copier l'URL fournie (ex: `https://camionsuf-backend.onrender.com`)
7. Dans Vercel → Settings → Environment Variables, ajouter :
   - `TRACKING_BACKEND_URL` = URL Render ci-dessus
   - `TRACKING_SECRET` = même valeur que dans `.env`

## Obtenir les tokens Meta

1. Allez sur https://developers.facebook.com/apps/
2. Créez una app de type **Business**
3. Ajoutez le produit **WhatsApp**
4. Dans *Configuration de l'API WhatsApp* :
   - Notez le **Phone Number ID**
   - Générez ou copiez le **Token d'accès temporaire** (valide 24h) ou créez un token permanent
5. Ajoutez votre numéro comme numéro de test si vous n'avez pas encore de compte WABA approuvé
