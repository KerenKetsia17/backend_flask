"""
CamionSuf — Backend Flask
Fournit l'API /track qui envoie des notifications WhatsApp via Meta Cloud API.
"""

from flask import Flask
from flask_cors import CORS
from routes.tracking import tracking_bp

app = Flask(__name__)
CORS(app)  # Permettre les appels depuis Vercel (api/notify.js)

app.register_blueprint(tracking_bp)


@app.get("/")
def health():
    return {"status": "ok", "service": "camionsuf-backend"}, 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
