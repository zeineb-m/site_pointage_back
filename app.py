from flask import Flask, jsonify, request
from flask_cors import CORS
import cv2
import face_recognition
import pyttsx3
import numpy as np
import io
from PIL import Image
from pymongo import MongoClient
from bson.binary import Binary
import logging
from datetime import datetime, time, timedelta
from bson.objectid import ObjectId
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import os
import uuid
from bson.regex import Regex
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import fitz  # PyMuPDF pour PDF
import pandas as pd
from reports_utils import generate_daily_reports, index_daily_reports, search_reports
from flask import request, jsonify, send_from_directory, abort
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

# ==========================
# CONNEXION MONGO
# ==========================
def mongo_connection():
    try:
        client = MongoClient("mongodb+srv://stage:stage@cluster0.gbm1c.mongodb.net/stage?retryWrites=true&w=majority")
        return client["stage"]
    except Exception as e:
        logging.error(f"Erreur de connexion à MongoDB: {e}")
        return None

# ==========================
# FONCTIONS FACIALES
# ==========================
def detect_faces(frame):
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb_small_frame)
    encodings = face_recognition.face_encodings(rgb_small_frame, locations)
    return locations, encodings

def recognize_person(encoding, known_faces, known_names):
    matches = face_recognition.compare_faces(known_faces, encoding)
    if True in matches:
        index = matches.index(True)
        return {"username": known_names[index]}
    return None

def reverse_geocode(lat, lon):
    try:
        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 18, 'addressdetails': 1}
        headers = {'User-Agent': 'mon-app-pointage/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('display_name', 'Adresse inconnue')
        else:
            logging.warning(f"Geocoding error HTTP {response.status_code}")
            return 'Erreur géocodage'
    except Exception as e:
        logging.error(f"Erreur géocodage inverse: {e}")
        return 'Erreur géocodage'

def load_known_faces_by_role(role):
    db = mongo_connection()
    if db is None:
        return [], [], {}

    known_faces, known_names, known_user_ids = [], [], {}

    try:
        users = db.user.find({"photo": {"$exists": True}, "role": role})
        for user in users:
            image_data = user.get('photo')
            if not image_data:
                continue
            image_bytes = bytes(image_data) if isinstance(image_data, Binary) else image_data
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            img_np = np.array(img)
            encodings = face_recognition.face_encodings(img_np)
            if not encodings:
                continue
            encoding = encodings[0]
            username = user.get("username", "Inconnu")
            known_faces.append(encoding)
            known_names.append(username)
            known_user_ids[username] = str(user.get("_id"))
    except Exception as e:
        logging.error(f"Erreur MongoDB : {e}")

    return known_faces, known_names, known_user_ids

# ==========================
# CAPTURE VIDÉO
# ==========================
def capture_video(duration=3):
    output_path = f"fraude_check_{uuid.uuid4().hex}.avi"
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Impossible d'ouvrir la caméra.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 20
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    start_time = datetime.now()
    while (datetime.now() - start_time).seconds < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    cap.release()
    out.release()
    return output_path

# ==========================
# ANALYSE FRAUDE (APPEL API EXTERNE)
# ==========================
def analyser_fraude(video_path, username=None):
    url = "http://localhost:5001/detect_fraude"

    try:
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {'username': username} if username else {}

            logging.info(f"📡 Envoi à {url} avec vidéo {video_path} et username={username}")
            response = requests.post(url, files=files, data=data, timeout=60)

            logging.info(f"📬 Statut HTTP: {response.status_code}")

            try:
                json_data = response.json()
                logging.info(f"✅ Réponse JSON : {json_data}")
                return json_data.get("fraude", False)
            except ValueError as json_err:
                logging.error(f"❌ Erreur décodage JSON : {json_err} | Texte brut : {response.text}")
                return None

    except requests.exceptions.Timeout:
        logging.error("⏰ Timeout lors de l'appel à /detect_fraude")
        return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f"🚨 Erreur réseau: {req_err}")
        return None
    except Exception as e:
        logging.error(f"🛑 Erreur générale : {e}")
        return None

# ==========================
# VÉRIFICATION DÉPART NON AUTORISÉ POUR JOUR PRÉCÉDENT (INTERNES & MANUELLES)
# ==========================
def verifier_depart_non_autorise_pour_jour_precedent(db, user_id, username, role, adresse):
    hier = datetime.now() - timedelta(days=1)
    jour_prec_debut = datetime(hier.year, hier.month, hier.day)
    jour_prec_fin = jour_prec_debut + timedelta(days=1)

    pointage_collection = db.pointage
    notification_collection = db.notification

    dernier_depart = pointage_collection.find_one(
        {
            "user_id": user_id,
            "date_pointage": {"$gte": jour_prec_debut, "$lt": jour_prec_fin},
            "statut": "depart"
        },
        sort=[("heure_depart", -1)]
    )
    if not dernier_depart:
        return

    heure_depart = dernier_depart.get("heure_depart") or dernier_depart.get("heure_pointage")
    if not heure_depart:
        return

    heure_depart_time = heure_depart.time()
    limite_jour = time(16, 0)
    limite_nuit = time(4, 0)

    if heure_depart_time < limite_jour or heure_depart_time < limite_nuit:
        exists = notification_collection.find_one({
            "user_id": user_id,
            "date": jour_prec_debut,
            "statut": "depart_non_autorise"
        })
        if exists:
            return

        notification_doc = {
            "user_id": user_id,
            "username": username,
            "date": jour_prec_debut,
            "heure": heure_depart,
            "statut": "depart_non_autorise",
            "message": f"Dernier départ hier non autorisé à {heure_depart.strftime('%H:%M:%S')}",
            "role": role,
            "adresse": adresse
        }
        notification_collection.insert_one(notification_doc)
        logging.info(f"Notification départ non autorisé créée pour user {username} hier.")

# ==========================
# ROUTE PRINCIPALE POINTAGE
# ==========================
@app.route('/get_person_data', methods=['POST'])
def get_person_data():
    video_capture = None
    engine = None
    try:
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')

        if None in [lat, lon]:
            return jsonify({"message": "Coordonnées manquantes"}), 400

        db = mongo_connection()
        if db is None:
            return jsonify({"message": "Erreur base de données"}), 500

        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)

        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            return jsonify({"message": "Erreur caméra"}), 500

        engine = pyttsx3.init()
        ret, frame = video_capture.read()
        if not ret:
            return jsonify({"message": "Erreur capture image"}), 500

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({"message": "Erreur encodage image"}), 500
        image_bytes = jpeg.tobytes()

        locations, encodings = detect_faces(frame)
        if not encodings:
            engine.say("Aucun visage détecté")
            engine.runAndWait()
            return jsonify({"statut": "non_reconnu", "message": "Aucun visage détecté"}), 200

        for encoding in encodings:
            for role in ["SITE_SUPERVISOR", "EMPLOYEE", "ADMIN"]:
                known_faces, known_names, known_user_ids = load_known_faces_by_role(role)
                user = recognize_person(encoding, known_faces, known_names)
                if user:
                    user_id_str = known_user_ids[user["username"]]
                    adresse = reverse_geocode(lat, lon)
                    video_path = capture_video()

                    fraude_detectee = analyser_fraude(video_path, user["username"])

                    if fraude_detectee:
                        db.fraude.insert_one({
                            "user_id": user_id_str,
                            "username": user["username"],
                            "date": now,
                            "role": role,
                            "adresse": adresse,
                            "message": "Fraude détectée lors du pointage",
                            "raisons": ["Analyse écran : téléphone détecté", "Analyse liveness : score faible"]
                        })

                        db.notification.insert_one({
                            "user_id": user_id_str,
                            "username": user["username"],
                            "date": now,
                            "heure": now,
                            "statut": "fraude",
                            "role": role,
                            "adresse": adresse,
                            "message": "Une fraude a été détectée (vidéo suspecte)"
                        })

                        logging.warning(f"🚨 Fraude détectée pour {user['username']}")
                    else:
                        logging.info(f"Pas de fraude détectée pour {user['username']}")

                    # Suppression fichier vidéo temporaire
                    try:
                        os.remove(video_path)
                    except Exception as e:
                        logging.warning(f"Erreur suppression fichier vidéo temporaire: {e}")

                    pointage_collection = db.pointage

                    pointage_doc = pointage_collection.find_one({
                        "user_id": user_id_str,
                        "date_pointage": {"$gte": today_start, "$lt": today_start + timedelta(days=1)}
                    })

                    if not pointage_doc:
                        statut = "arrivee"
                    else:
                        nb_arrivees = len(pointage_doc.get("arrivees", []))
                        nb_departs = len(pointage_doc.get("departs", []))
                        statut = "arrivee" if nb_arrivees <= nb_departs else "depart"

                    if statut == "arrivee":
                        verifier_depart_non_autorise_pour_jour_precedent(
                            db, user_id_str, user["username"], role, adresse
                        )

                        pointage_collection.update_one(
                            {
                                "user_id": user_id_str,
                                "date_pointage": {"$gte": today_start, "$lt": today_start + timedelta(days=1)}
                            },
                            {
                                "$setOnInsert": {
                                    "user_id": user_id_str,
                                    "username": user["username"],
                                    "date_pointage": today_start,
                                    "role": role
                                },
                                "$push": {"arrivees": {"heure": now}},
                                "$set": {
                                    "image": Binary(image_bytes),
                                    "adresse": adresse,
                                    "localisation": {"lat": lat, "lon": lon}
                                }
                            },
                            upsert=True
                        )
                    else:  # depart
                        pointage_collection.update_one(
                            {
                                "user_id": user_id_str,
                                "date_pointage": {"$gte": today_start, "$lt": today_start + timedelta(days=1)}
                            },
                            {
                                "$push": {"departs": {"heure": now}},
                                "$set": {
                                    "adresse": adresse,
                                    "localisation": {"lat": lat, "lon": lon}
                                }
                            }
                        )

                    final_doc = pointage_collection.find_one({
                        "user_id": user_id_str,
                        "date_pointage": {"$gte": today_start, "$lt": today_start + timedelta(days=1)}
                    })
                    heures_arrivee = [a["heure"].strftime("%H:%M:%S") for a in final_doc.get("arrivees", [])]
                    heures_depart = [d["heure"].strftime("%H:%M:%S") for d in final_doc.get("departs", [])]

                    engine.say(f"{user['username']}, statut {statut} enregistré.")
                    engine.runAndWait()

                    return jsonify({
                        "username": user["username"],
                        "statut": statut,
                        "adresse": adresse,
                        "role": role,
                        "heures_arrivee": heures_arrivee,
                        "heures_depart": heures_depart,
                        "fraude": fraude_detectee,
                        "raisons": ["Fraude vidéo détectée"] if fraude_detectee else []
                    }), 200

        engine.say("Visage non reconnu.")
        engine.runAndWait()
        return jsonify({"statut": "non_reconnu", "message": "Visage non reconnu."}), 200

    except Exception as e:
        logging.error(f"Erreur reconnaissance : {e}")
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        if video_capture:
            video_capture.release()
        if engine:
            engine.stop()
@app.route('/fraudes', methods=['GET'])
def get_fraudes():
    db = mongo_connection()
    if db is None:
        return jsonify({"message": "Erreur base de données"}), 500

    try:
        # On récupère les 50 dernières fraudes, triées par date décroissante
        fraudes_cursor = db.fraude.find().sort("date", -1).limit(50)
        fraudes_list = []
        for f in fraudes_cursor:
            fraudes_list.append({
                "id": str(f.get("_id")),
                "user_id": f.get("user_id"),
                "username": f.get("username"),
                "date": f.get("date").isoformat() if f.get("date") else None,
                "role": f.get("role"),
                "adresse": f.get("adresse"),
                "message": f.get("message"),
                "raisons": f.get("raisons", [])
            })
        return jsonify(fraudes_list), 200
    except Exception as e:
        logging.error(f"Erreur récupération fraudes : {e}")
        return jsonify({"message": "Erreur serveur"}), 500
def envoyer_mail_fraude(destinataire, nom_utilisateur, type_fraude, date_fraude, raisons):
    expediteur = "tonemail@gmail.com"
    mot_de_passe = "motdepasseoumotdepasseapplication"

    sujet = f"⚠️ Fraude détectée - {nom_utilisateur}"
    corps = f"""
Bonjour,

Une fraude a été détectée.

👤 Utilisateur : {nom_utilisateur}
📅 Date : {date_fraude}
🚨 Type : {type_fraude}
📌 Raisons : {", ".join(raisons)}

Merci de prendre les mesures nécessaires.

Cordialement,
Le système de détection
"""

    message = MIMEMultipart()
    message["From"] = expediteur
    message["To"] = destinataire
    message["Subject"] = sujet
    message.attach(MIMEText(corps, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            serveur.send_message(message)
        print("✅ Mail envoyé avec succès.")
    except Exception as e:
        print(f"❌ Erreur d'envoi du mail : {e}")
# ==========================
# VERIFICATION DES DEPARTS NON AUTORISES (INTERNE)
# ==========================
def verifier_depart_non_autorise_interne(check_date=None):
    db = mongo_connection()
    if db is None:
        logging.error("Erreur base de données")
        return

    if check_date is None:
        check_date = datetime.now()

    jour_prec = check_date - timedelta(days=1)
    jour_prec_debut = datetime(jour_prec.year, jour_prec.month, jour_prec.day)
    jour_prec_fin = jour_prec_debut + timedelta(days=1)

    pointage_collection = db.pointage
    notification_collection = db.notification

    # Récupération des départs
    results = pointage_collection.find({
        "date_pointage": {"$gte": jour_prec_debut, "$lt": jour_prec_fin},
        "statut": "depart"
    })

    for depart in results:
        heure_depart = depart.get("heure_depart") or depart.get("heure_pointage")
        if not heure_depart:
            continue

        heure_depart_time = heure_depart.time()
        limite = time(16, 0) if time(7, 30) <= heure_depart_time <= time(17, 30) else time(4, 0)

        if heure_depart_time < limite:
            exists = notification_collection.find_one({
                "user_id": depart["user_id"],
                "date": jour_prec_debut,
                "statut": "depart_non_autorise"
            })
            if exists:
                continue

            notification_doc = {
                "user_id": depart["user_id"],
                "username": depart.get("username", ""),
                "date": jour_prec_debut,
                "heure": heure_depart,
                "statut": "depart_non_autorise",
                "message": f"Départ non autorisé à {heure_depart.strftime('%H:%M:%S')}",
                "role": depart.get("role", ""),
                "adresse": depart.get("adresse", "")
            }
            notification_collection.insert_one(notification_doc)
            logging.info(f"Notification départ non autorisé créée pour {depart.get('username', '')}.")

    logging.info("✅ Vérification départs non autorisés terminée")

# ==========================
# VERIFICATION ABSENCES
# ==========================
def verifier_absences_fin_journee():
    db = mongo_connection()
    if db is None:
        logging.error("Erreur base de données")
        return

    user_collection = db.user
    pointage_collection = db.pointage
    notification_collection = db.notification

    now = datetime.now()
    jour_prec = now - timedelta(days=1)
    jour_prec_debut = datetime(jour_prec.year, jour_prec.month, jour_prec.day)
    jour_prec_fin = jour_prec_debut + timedelta(days=1)

    users = list(user_collection.find({"role": {"$ne": "ADMIN"}}))

    for user in users:
        user_id = str(user["_id"])

        count = pointage_collection.count_documents({
            "user_id": user_id,
            "date_pointage": {"$gte": jour_prec_debut, "$lt": jour_prec_fin}
        })

        if count == 0:
            exists = notification_collection.find_one({
                "user_id": user_id,
                "date": jour_prec_debut,
                "statut": "absent"
            })
            if exists:
                continue

            notif = {
                "user_id": user_id,
                "username": user.get("username", "Inconnu"),
                "date": jour_prec_debut,
                "statut": "absent",
                "message": "Absence détectée (pas de pointage sur 24h)",
                "role": user.get("role", ""),
                "adresse": ""
            }
            notification_collection.insert_one(notif)
            logging.info(f"Notification absence créée pour user {user.get('username', 'Inconnu')}")

# ==========================
# ROUTES MANUELLES
# ==========================
@app.route('/verifier_depart_non_autorise', methods=['POST'])
def verifier_depart_non_autorise_route():
    try:
        data = request.get_json() or {}
        date_str = data.get("date")
        check_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
        verifier_depart_non_autorise_interne(check_date)
        return jsonify({"message": f"Vérification terminée pour {check_date.strftime('%Y-%m-%d')}"}), 200
    except Exception as e:
        logging.error(f"Erreur route vérification départs : {e}")
        return jsonify({"message": "Erreur serveur"}), 500

@app.route('/verifier_fin_journee', methods=['POST'])
def verifier_fin_journee_route():
    try:
        verifier_absences_fin_journee()
        return jsonify({"message": "Vérification des absences terminée"}), 200
    except Exception as e:
        logging.error(f"Erreur vérification fin journée : {e}")
        return jsonify({"message": "Erreur serveur"}), 500

# ==========================
# SCHEDULER
# ==========================
def verifier_toutes_les_verifications():
    logging.info("Début des vérifications combinées")
    verifier_depart_non_autorise_interne(datetime.now() - timedelta(days=1))
    verifier_absences_fin_journee()
    generate_daily_reports()
    index_daily_reports()
    logging.info("Fin des vérifications combinées")

scheduler = BackgroundScheduler(timezone='Africa/Tunis')
scheduler.add_job(
    func=verifier_toutes_les_verifications,
    trigger='cron',
    hour=6,
    minute=0,
    id='verification_combinee_job',
    name='Vérification départs non autorisés + absences',
    replace_existing=True
)
scheduler.start()
logging.info("🗓️ Planificateur initialisé à 6h00")

# Endpoint recherche RAG simple
@app.route('/search', methods=['POST'])
def search_route():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Query manquante"}), 400
    results = search_reports(query)
    return jsonify({"results": results})

# Endpoint téléchargement rapports
@app.route('/reports/<filename>', methods=['GET'])
def download_report(filename):
    reports_dir = os.path.join(os.getcwd(), 'reports')
    if os.path.exists(os.path.join(reports_dir, filename)):
        return send_from_directory(reports_dir, filename, as_attachment=True)
    else:
        abort(404)




if __name__ == '__main__':
    app.run(debug=True, port=5010)
