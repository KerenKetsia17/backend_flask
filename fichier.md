# WhatsApp Bot — Sotilma Farm & CamionSouf
Flask + WhatsApp Cloud API + Mistral AI

---

## Structure

```
app.py                        
requirements.txt
.env.example

config/
  sotilma_prompt.py           # System prompt Sotilma (Mistral)
  sotilma_catalogue.py        # Produits, devis, format texte

routes/
  sotilma.py                  # Blueprint /webhook/sotilma
  tracking.py                 # Blueprint /track (suivi commande)

services/
  whatsapp.py                 # Tous les types de messages WA natifs
  session.py                  # Historique + meta par utilisateur (RAM)
  ai.py                       # detect_intent / generate_response / extract_info
```

| Service     | URL webhook                                 | Verify token            |
|-------------|---------------------------------------------|-------------------------|
| Sotilma     | `https://votre-domaine.com/webhook/sotilma` | `WHATSAPP_VERIFY_TOKEN` |
| CamionSouf  | `https://votre-domaine.com/tracking/order`  | `WHATSAPP_VERIFY_TOKEN` |

Les deux services utilisent le **même** `WHATSAPP_VERIFY_TOKEN`
mais des **Phone Number IDs et Access Tokens différents**.

Champs à activer dans Meta : `messages`

---

## Route de suivi CamionSouf — `/track`

Accepte POST.

| Paramètre | Obligatoire | Description |
|-----------|-------------|-------------|
| `phone`   | oui | Numéro client (ex: `221771234567`, sans `+`) |
| `message` | oui | Texte à envoyer au client |
| `url`     | non | Lien de suivi en direct (ex: Google Maps live) |
| `secret`  | oui* | Clé `TRACKING_SECRET` du `.env` |

*Si `TRACKING_SECRET` est vide, la protection est désactivée.

### Exemples

```bash
# GET
curl "https://votre-domaine.com/track?phone=221771234567&message=Votre+camion+est+en+route&url=https://maps.example.com/CMD001&secret=MON_SECRET"

# POST JSON
curl -X POST https://votre-domaine.com/track \
  -H "Content-Type: application/json" \
  -d '{"phone":"221771234567","message":"Livraison confirmee, merci !","secret":"MON_SECRET"}'
```

### Réponse

```json
{
  "success": true,
  "phone": "221771234567",
  "preview": "CAMIONSOUF — Suivi de commande\n============================\nVotre camion est en route..."
}
```

---

## Messages natifs WhatsApp utilisés

| Type        | Quand                                     |
|-------------|-------------------------------------------|
| `text`      | Toutes les réponses conversationnelles    |
| `list`      | Catalogue Sotilma (V1/V2),                |
| `buttons`   | Choix modèle, confirmation devis/commande |
| `location`  | GPS pin Sotilma Farm (Keur Massar)        |

---

## Logique Sotilma — états de conversation

```
AUCUN ETAT
  → greeting       : message d'accueil
  → show_catalogue : liste interactive V1 / V2
  → product_info   : fiche produit + boutons
  → request_quote  : passe en état "collecting_quote"

collecting_quote  (machine à états)
  → demande nom → email → telephone → adresse
  → (une seule info par message, jamais redemander ce qui est déjà connu)
  → quand tout est rempli : envoie le devis formaté + bouton confirmation
```

---

## Variables d'environnement

Voir `.env` pour la liste complète.