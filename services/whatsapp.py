"""
Service d'envoi de messages WhatsApp via Meta Cloud API.
Doc : https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
GRAPH_API_URL = "https://graph.facebook.com/v19.0"


def send_text(phone: str, message: str) -> dict:
    """
    Envoie un message texte WhatsApp à `phone` (format international, sans +).
    Ex : phone = "221771234567"

    Retourne la réponse JSON de l'API Meta ou lève une exception en cas d'erreur.
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise EnvironmentError(
            "WHATSAPP_ACCESS_TOKEN et WHATSAPP_PHONE_NUMBER_ID doivent être définis dans .env"
        )

    url = f"{GRAPH_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {
            "preview_url": True,   # Génère automatiquement un aperçu du lien
            "body": message,
        },
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)

    if not response.ok:
        raise RuntimeError(
            f"Meta API error {response.status_code}: {response.text}"
        )

    return response.json()
