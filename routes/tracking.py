"""
Blueprint /track — CamionSouf
Reçoit un appel POST (depuis api/notify.js sur Vercel ou tout autre client)
et déclenche l'envoi d'une notification WhatsApp au client.
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.whatsapp import send_text_message

tracking_bp = Blueprint("tracking", __name__)
logger = logging.getLogger(__name__)

TRACKING_SECRET = os.environ.get("TRACKING_SECRET", "")


def _normalize_phone(phone: str) -> str:
    """Conserve uniquement les chiffres du numéro client."""
    return "".join(ch for ch in (phone or "") if ch.isdigit())


@tracking_bp.route("/track", methods=["GET", "POST"])
def track():
    """
    Paramètres (query-string ou body JSON) :
      - phone   : numéro du client (ex: 221771234567, sans +)
      - message : texte de la notification
      - url     : lien de suivi en direct (optionnel)
      - secret  : clé TRACKING_SECRET partagée
    """
    # Accepte GET (query-string) et POST (JSON ou form)
    if request.method == "GET":
        data = request.args
    else:
        data = request.get_json(silent=True) or request.form

    phone = _normalize_phone((data.get("phone") or "").strip())
    message = (data.get("message") or "").strip()
    url = (data.get("url") or "").strip()
    secret = (data.get("secret") or "").strip()

    # ── Authentification ──────────────────────────────────────────────────────
    if TRACKING_SECRET and secret != TRACKING_SECRET:
        logger.warning("Tentative non autorisée sur /track (secret invalide)")
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # ── Validation ────────────────────────────────────────────────────────────
    if not phone or not message:
        return jsonify({"success": False, "error": "Les champs 'phone' et 'message' sont obligatoires"}), 400

    # ── Construction du message WhatsApp ──────────────────────────────────────
    separator = "=" * 28
    body = f"CAMIONSOUF — Suivi de commande\n{separator}\n{message}"
    if url:
        body += f"\n\n📍 Suivi en direct : {url}"

    # ── Envoi WhatsApp ────────────────────────────────────────────────────────
    try:
        wa_result = send_text_message(phone, body)
        logger.info("Notification envoyée à %s", phone)
        return jsonify({"success": True, "phone": phone, "preview": body, "wa": wa_result}), 200
    except PermissionError as exc:
        logger.error("Erreur d'autorisation WhatsApp : %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 502
    except Exception as exc:
        logger.error("Erreur envoi WhatsApp vers %s : %s", phone, exc)
        return jsonify({"success": False, "error": str(exc)}), 500
