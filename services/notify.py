"""
notification_service.py
=======================
Service CamionSouf — envoi des notifications WhatsApp à chaque progression de 25%.
À appeler depuis le backend Flask lors de la mise à jour du statut d'une livraison.
"""

import os
from typing import Optional
import requests

# URL de l'API de tracking (backend WhatsApp)
TRACKING_URL = os.getenv("TRACKING_URL", "https://votre-domaine.com/track")
TRACKING_SECRET = os.getenv("TRACKING_SECRET", "")

# ─── Templates de messages par étape ─────────────────────────────────────────
# {zone}  → quartier/ville actuel du livreur  (ex: "Pikine")
# {temps} → estimation d'arrivée              (ex: "15 minutes")

TEMPLATES_PROGRESSION = {
    25: (
        "Bonjour ! Votre commande est en route.\n"
        "Notre livreur vient de partir de {zone_txt}.\n"
        "Vous le recevrez{temps_txt}. 🚛"
    ),
    50: (
        "Bonne nouvelle ! 📦 Votre livraison avance bien.\n"
        "Le camion est actuellement{zone_txt} et se rapproche de vous.\n"
        "Arrivée prévue{temps_txt}. Tenez-vous prêt(e) ! 😊"
    ),
    75: (
        "Votre commande est presque là ! ⏳\n"
        "Le livreur est{zone_txt} et arrive chez vous{temps_txt}.\n"
        "Soyez disponible pour réceptionner votre colis. 🙏"
    ),
    100: (
        "C'est livré ! ✅\n"
        "Votre commande CamionSouf a bien été remise.\n"
        "Merci de nous avoir fait confiance. À bientôt ! 🎉"
    ),
}


def _construire_message(progression: int, zone: Optional[str], temps: Optional[str]) -> str:
    """Injecte la zone et le temps estimé dans le template du message."""
    zone_txt  = f" à {zone}"    if zone  else ""
    temps_txt = f" dans {temps}" if temps else " très prochainement"

    return TEMPLATES_PROGRESSION[progression].format(
        zone_txt=zone_txt,
        temps_txt=temps_txt,
    )


# ─── Fonction principale ───────────────────────────────────────────────────────

def envoyer_notification_progression(
    telephone_client: str,
    progression: int,
    lien_suivi: Optional[str] = None,
    zone_actuelle: Optional[str] = None,
    temps_estime: Optional[str] = None,
) -> dict:
    """
    Envoie une notification WhatsApp au client pour une progression donnée.

    Paramètres :
        telephone_client — numéro sans +      (ex: "221771234567")
        progression      — 25, 50, 75 ou 100
        lien_suivi       — URL Google Maps live (optionnel pour 100%)
        zone_actuelle    — quartier/ville du livreur  (ex: "Pikine")
        temps_estime     — estimation d'arrivée       (ex: "15 minutes")

    Retourne :
        dict avec "success" (bool) et "detail" (str)
    """
    if progression not in TEMPLATES_PROGRESSION:
        return {
            "success": False,
            "detail": f"Progression invalide : {progression}. Valeurs acceptées : 25, 50, 75, 100",
        }

    message = _construire_message(progression, zone_actuelle, temps_estime)

    payload = {
        "phone":   telephone_client,
        "message": message,
        "secret":  TRACKING_SECRET,
    }

    if lien_suivi:
        payload["url"] = lien_suivi

    try:
        response = requests.post(TRACKING_URL, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get("success"):
            print(f"[CamionSouf] ✅ Notification {progression}% envoyée → {telephone_client}")
            return {"success": True, "detail": f"Notification {progression}% envoyée"}

        # Cas 401 : secret invalide
        if response.status_code == 401:
            return {"success": False, "detail": "Secret invalide — vérifiez TRACKING_SECRET"}

        return {"success": False, "detail": data.get("error", "Erreur inconnue")}

    except requests.exceptions.Timeout:
        return {"success": False, "detail": "Timeout — le serveur de tracking ne répond pas"}
    except requests.exceptions.RequestException as exc:
        return {"success": False, "detail": f"Erreur réseau : {exc}"}


# ─── Exemple d'intégration dans une route Flask ───────────────────────────────
#
# from flask import Blueprint, request, jsonify
# from services.notification_service import envoyer_notification_progression
#
# bp = Blueprint("livraisons", __name__)
#
# PROGRESSION_PAR_STATUT = {
#     "en_route":  25,
#     "mi_chemin": 50,
#     "proche":    75,
#     "livre":    100,
# }
#
# @bp.route("/livraisons/<int:id>/statut", methods=["PUT"])
# def mettre_a_jour_statut(id):
#     data = request.get_json()
#     progression   = PROGRESSION_PAR_STATUT.get(data.get("statut"))
#     telephone     = data.get("telephone_client")
#     lien_suivi    = data.get("lien_suivi")
#     zone_actuelle = data.get("zone_actuelle")   # ex: "Pikine"
#     temps_estime  = data.get("temps_estime")    # ex: "15 minutes"
#
#     if progression and telephone:
#         envoyer_notification_progression(
#             telephone, progression, lien_suivi,
#             zone_actuelle=zone_actuelle,
#             temps_estime=temps_estime,
#         )
#
#     return jsonify({"success": True})


# ─── Test rapide : python services/notification_service.py ────────────────────

if __name__ == "__main__":
    TEST_PHONE = "221785297857"
    TEST_LIEN  = "https://maps.example.com/CMD001"

    scenarios = [
        (25,  TEST_LIEN, "Thiaroye",    "30 minutes"),
        (50,  TEST_LIEN, "Pikine",      "15 minutes"),
        (75,  TEST_LIEN, "Keur Massar", "5 minutes"),
        (100, None,      None,          None),
    ]

    for etape, lien, zone, temps in scenarios:
        resultat = envoyer_notification_progression(
            TEST_PHONE, etape, lien,
            zone_actuelle=zone,
            temps_estime=temps,
        )
        print(f"  Étape {etape}% → {resultat}")
