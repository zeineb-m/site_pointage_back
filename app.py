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
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json().get('display_name', 'Adresse inconnue')
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
# VÉRIFICATION DÉPART NON AUTORISÉ
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
# ROUTE POINTAGE
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
        current_time = now.time()
        today_start = datetime(now.year, now.month, now.day)

        autorise = (
            (time(7, 30) <= current_time <= time(17, 30)) or
            (current_time >= time(19, 0) or current_time < time(5, 0))
        )

        if not autorise:
            engine = pyttsx3.init()
            engine.say("Pointage non autorisé à cette heure.")
            engine.runAndWait()
            return jsonify({"message": "⛔ Pointage non autorisé à cette heure"}), 403

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
                        "heures_depart": heures_depart
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
        limite = time(16, 0) if heure_depart_time >= time(7, 30) and heure_depart_time <= time(17, 30) else time(4, 0)

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

    logging.info(f"✅ Vérification départs non autorisés terminée")

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
    logging.info("Fin des vérifications combinées")

scheduler = BackgroundScheduler(timezone='Africa/Tunis')
scheduler.add_job(
    func=verifier_toutes_les_verifications,
    trigger='cron',
    hour=13,
    minute=26,
    id='verification_combinee_job',
    name='Vérification départs non autorisés + absences',
    replace_existing=True
)
scheduler.start()
logging.info("🗓️ Planificateur initialisé à 6h00")

if __name__ == '__main__':
    app.run(debug=True, port=5010)
