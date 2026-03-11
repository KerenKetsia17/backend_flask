"""
Service WhatsApp — CamionSouf
Envoie des messages via l'API Meta WhatsApp Cloud.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

_WA_BASE_URL = "https://graph.facebook.com/v22.0"


def _normalize_phone(phone: str) -> str:
    """Conserve uniquement les chiffres (supprime +, espaces, tirets...)."""
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def _get_credentials() -> tuple[str, str]:
    """Lit les credentials depuis les variables d'environnement."""
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_id:
        raise EnvironmentError(
            "WHATSAPP_ACCESS_TOKEN et WHATSAPP_PHONE_NUMBER_ID doivent être définis."
        )
    return token, phone_id


def send_text_message(to: str, body: str) -> dict:
    """
    Envoie un message texte WhatsApp à un numéro donné.

    :param to:   Numéro destinataire au format international sans '+' (ex: 221771234567)
    :param body: Contenu du message (max 4096 caractères)
    :returns:    Réponse JSON de l'API Meta
    :raises requests.HTTPError: si l'API répond avec un code d'erreur
    """
    access_token, phone_number_id = _get_credentials()
    normalized_to = _normalize_phone(to)

    if not normalized_to:
        raise ValueError("Numéro destinataire invalide (aucun chiffre détecté).")

    url = f"{_WA_BASE_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_to,
        "type": "text",
        "text": {
            "body": body,
            "preview_url": False,
        },
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)

    if response.status_code == 401:
        raise PermissionError(
            "Token WhatsApp expiré ou invalide. "
            "Renouvelez WHATSAPP_ACCESS_TOKEN sur Meta Developers → WhatsApp → Configuration API."
        )
    if response.status_code == 403:
        raise PermissionError(
            "Accès refusé par l'API Meta (403). Vérifiez les permissions du token et du numéro."
        )

    if response.status_code >= 400:
        try:
            error_payload = response.json()
            meta_error = error_payload.get("error", {})
            message = meta_error.get("message") or "Erreur inconnue"
            code = meta_error.get("code")
            subcode = meta_error.get("error_subcode")
            fbtrace = meta_error.get("fbtrace_id")
            raise requests.HTTPError(
                f"Meta API error: {message} (code={code}, subcode={subcode}, fbtrace_id={fbtrace})"
            )
        except ValueError:
            # Réponse non JSON
            response.raise_for_status()

    response.raise_for_status()
    return response.json()
