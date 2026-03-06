"""
routes/tracking.py — Route POST /track

Ce fichier est le point d'entrée HTTP du backend Flask.
Il reçoit les requêtes envoyées par Vercel (api/notify.js) lorsqu'un jalon
de livraison (25 %, 50 %, 75 %, 100 %) est atteint côté frontend.

Flux complet :
  SuiviPage.jsx → fetch('/api/notify')
      → api/notify.js (Vercel serverless)
          → POST /track  ← on est ici
              → services/whatsapp.py
                  → Meta WhatsApp Cloud API
                      → 📱 Message reçu par le client

Corps JSON attendu :
  {
    "secret":   "<TRACKING_SECRET>",      # clé de sécurité partagée avec Vercel
    "phone":    "221771234567",            # numéro client sans + (format international)
    "message":  "Votre commande...",       # texte de la notification
    "url":      "https://...suivi?cmd=..." # lien de suivi (optionnel à 100 %)
  }
"""

import os
from flask import Blueprint, request, jsonify
from services.whatsapp import send_text
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env (en local)
# Sur Render, elles sont injectées directement par la plateforme
load_dotenv()

# Crée un Blueprint Flask — permet de regrouper cette route séparément de app.py
tracking_bp = Blueprint("tracking", __name__)

# Lit le secret depuis les variables d'environnement
# Ce secret doit être identique à TRACKING_SECRET dans Vercel
TRACKING_SECRET = os.environ.get("TRACKING_SECRET", "")


@tracking_bp.post("/track")
def track():
    # Lit le corps JSON de la requête (envoyée par api/notify.js côté Vercel)
    # silent=True évite une exception si le corps n'est pas du JSON valide
    data = request.get_json(silent=True) or {}

    # ── 1. Vérification du secret ─────────────────────────────────────────
    # Sécurité : empêche n'importe qui d'appeler /track directement
    if not TRACKING_SECRET:
        # Le serveur lui-même n'est pas configuré → erreur 500
        return jsonify({"error": "TRACKING_SECRET non configuré sur le serveur"}), 500

    if data.get("secret") != TRACKING_SECRET:
        # Secret incorrect → accès refusé (403 Forbidden)
        return jsonify({"error": "Secret invalide"}), 403

    # ── 2. Validation des paramètres ──────────────────────────────────────
    # Nettoie le numéro : supprime les espaces et le signe + éventuel
    phone = (data.get("phone") or "").replace(" ", "").replace("+", "")
    message = (data.get("message") or "").strip()
    url = (data.get("url") or "").strip()  # lien de suivi (peut être vide)

    if not phone or len(phone) < 7:
        return jsonify({"error": "Numéro de téléphone invalide ou manquant"}), 400

    if not message:
        return jsonify({"error": "Message manquant"}), 400

    # ── 3. Construction du message final ──────────────────────────────────
    full_message = message
    if url:
        # Ajoute le lien de suivi à la fin du message si fourni (pas à 100 % = livré)
        full_message += f"\n\n🔗 Suivre ma livraison en direct :\n{url}"

    # ── 4. Envoi WhatsApp via services/whatsapp.py ────────────────────────
    try:
        # Appelle la fonction qui contacte l'API Graph de Meta
        result = send_text(phone, full_message)
    except EnvironmentError as exc:
        # Variables WHATSAPP_ACCESS_TOKEN ou WHATSAPP_PHONE_NUMBER_ID manquantes
        return jsonify({"error": str(exc)}), 500
    except RuntimeError as exc:
        # L'API Meta a retourné une erreur (token expiré, numéro non enregistré…)
        return jsonify({"error": str(exc)}), 502

    # Retourne une confirmation au frontend avec un aperçu du message envoyé
    return jsonify({
        "success": True,
        "phone": phone,                                                          # numéro destinataire
        "preview": full_message[:120] + ("…" if len(full_message) > 120 else ""),# début du message
        "meta": result,                                                          # réponse brute Meta API
    }), 200
