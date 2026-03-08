"""
CamionSuf — Backend Flask
Fournit l'API /track qui envoie des notifications WhatsApp via Meta Cloud API.
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from routes.tracking import tracking_bp
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS : autorise uniquement les appels depuis Vercel (api/notify.js est server-side,
# donc CORS ne s'applique pas aux requêtes Node→Flask, mais on le configure
# pour les éventuels appels navigateur directs en développement).
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://camionsuf.vercel.app")
CORS(app, origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:4173"])

app.register_blueprint(tracking_bp)


@app.get("/")
def health():
    """Endpoint de vérification de santé (Render vérifie cette route)."""
    configured = bool(
        os.environ.get("WHATSAPP_ACCESS_TOKEN") and
        os.environ.get("WHATSAPP_PHONE_NUMBER_ID") and
        os.environ.get("TRACKING_SECRET")
    )
    return {
        "status": "ok",
        "service": "camionsuf-backend",
        "whatsapp_configured": configured,
    }, 200


if __name__ == "__main__":
    # Avertissement si les variables critiques manquent en développement
    missing = [v for v in ("WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "TRACKING_SECRET")
               if not os.environ.get(v)]
    if missing:
        logger.warning("Variables manquantes dans .env : %s", ", ".join(missing))
    app.run(debug=True, port=5000)
