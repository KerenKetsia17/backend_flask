"""
Service d'envoi de messages WhatsApp via Meta Cloud API.
Doc : https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Token d'accès à l'API Meta (obtenu sur developers.facebook.com → votre app WhatsApp)
# Peut être temporaire (24h) ou permanent (System User Token)
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")

# Identifiant du numéro de téléphone WhatsApp Business enregistré sur Meta
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")

# URL de base de l'API Graph de Meta
GRAPH_API_URL = "https://graph.facebook.com/v22.0"


def send_text(phone: str, message: str) -> dict:
    """
    Envoie un message texte WhatsApp à `phone` via Meta Cloud API.

    Paramètres :
        phone   — numéro international sans + ni espaces (ex: "221771234567")
        message — texte à envoyer (supporte les emojis et les sauts de ligne)

    Retourne le JSON de réponse de Meta (contient l'ID du message envoyé).
    Lève EnvironmentError si les variables d'env sont manquantes.
    Lève RuntimeError si l'API Meta retourne une erreur HTTP.
    """
    # Vérifie que les variables d'environnement ont bien été définies
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise EnvironmentError(
            "WHATSAPP_ACCESS_TOKEN et WHATSAPP_PHONE_NUMBER_ID doivent être définis dans .env"
        )

    # Construction de l'URL de l'endpoint Meta pour envoyer un message
    # Format : https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages
    url = f"{GRAPH_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    # Corps de la requête selon la spécification Meta Cloud API
    payload = {
        "messaging_product": "whatsapp",  # obligatoire, indique qu'on utilise WhatsApp
        "recipient_type": "individual",   # envoi à une seule personne (pas un groupe)
        "to": phone,                      # numéro destinataire (format E.164 sans +)
        "type": "text",                   # type de message : texte simple
        "text": {
            "preview_url": True,          # Meta génère automatiquement un aperçu du lien de suivi
            "body": message,              # contenu du message WhatsApp
        },
    }

    # En-têtes HTTP : authentification Bearer + type JSON
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",  # token d'accès Meta
        "Content-Type": "application/json",
    }

    # Envoi de la requête POST vers l'API Meta (timeout 10 s pour éviter les blocages)
    response = requests.post(url, json=payload, headers=headers, timeout=10)

    # Si l'API retourne un code d'erreur HTTP (4xx / 5xx) → on lève une exception
    # Exemple d'erreur : token expiré (401), numéro non enregistré (400)
    if not response.ok:
        raise RuntimeError(
            f"Meta API error {response.status_code}: {response.text}"
        )

    # Retourne la réponse JSON de Meta (contient messages[0].id si succès)
    return response.json()
