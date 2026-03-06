"""Ce fichier sert de route API dans le backend Flask qui permet à la plateforme d’envoyer automatiquement un message WhatsApp au client lorsqu’une étape de la livraison est atteinte."""


"""
Route POST /track — Reçoit les notifications de progression de livraison
et envoie un message WhatsApp au client via Meta Cloud API.

Corps attendu (JSON) :
  {
    "secret":   "<TRACKING_SECRET>",
    "phone":    "221771234567",     // numéro sans +
    "message":  "Votre commande...",
    "url":      "https://camionsuf.vercel.app/suivi?cmd=CMD-XXX"  // optionnel
  }
"""

import os
from flask import Blueprint, request, jsonify
from services.whatsapp import send_text
from dotenv import load_dotenv

load_dotenv()

tracking_bp = Blueprint("tracking", __name__)

TRACKING_SECRET = os.environ.get("TRACKING_SECRET", "")


@tracking_bp.post("/track")
def track():
    data = request.get_json(silent=True) or {}

    # ── 1. Vérification du secret ─────────────────────────────────────────
    if not TRACKING_SECRET:
        return jsonify({"error": "TRACKING_SECRET non configuré sur le serveur"}), 500

    if data.get("secret") != TRACKING_SECRET:
        return jsonify({"error": "Secret invalide"}), 403

    # ── 2. Validation des paramètres ──────────────────────────────────────
    phone = (data.get("phone") or "").replace(" ", "").replace("+", "")
    message = (data.get("message") or "").strip()
    url = (data.get("url") or "").strip()

    if not phone or len(phone) < 7:
        return jsonify({"error": "Numéro de téléphone invalide ou manquant"}), 400

    if not message:
        return jsonify({"error": "Message manquant"}), 400

    # ── 3. Construction du message final ──────────────────────────────────
    full_message = message
    if url:
        full_message += f"\n\n🔗 Suivre ma livraison en direct :\n{url}"

    # ── 4. Envoi WhatsApp ─────────────────────────────────────────────────
    try:
        result = send_text(phone, full_message)
    except EnvironmentError as exc:
        return jsonify({"error": str(exc)}), 500
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify({
        "success": True,
        "phone": phone,
        "preview": full_message[:120] + ("…" if len(full_message) > 120 else ""),
        "meta": result,
    }), 200
