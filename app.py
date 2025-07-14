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

def mongo_connection():
    try:
        client = MongoClient("mongodb+srv://stage:stage@cluster0.gbm1c.mongodb.net/stage?retryWrites=true&w=majority")
        return client["stage"]
    except Exception as e:
        logging.error(f"Erreur de connexion à MongoDB: {e}")
        return None

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

def verifier_depart_non_autorise_pour_jour_precedent(db, user_id, username, role, adresse):
    """
    Vérifie si le dernier départ d’hier est avant 11h (jour) ou 4h (nuit),
    et ajoute une notification depart_non_autorise si besoin.
    """
    pointage_collection = db.pointage
    notification_collection = db.notification

    hier = datetime.now() - timedelta(days=1)
    day_start = datetime(hier.year, hier.month, hier.day)
    day_end = datetime(hier.year, hier.month, hier.day, 23, 59, 59)

    # Cherche le dernier départ hier
    dernier_depart = pointage_collection.find_one(
        {
            "user_id": user_id,
            "date_pointage": {"$gte": day_start, "$lt": day_end},
            "statut": "depart"
        },
        sort=[("heure_depart", -1)]
    )
    if not dernier_depart:
        return  # Pas de départ hier

    heure_depart = dernier_depart.get("heure_depart") or dernier_depart.get("heure_pointage")
    if not heure_depart:
        return

    heure_depart_time = heure_depart.time()
    # Conditions horaires strictes pour notification
    if heure_depart_time < time(11, 0) or heure_depart_time < time(4, 0):
        # Vérifie si notification existe déjà
        exists = notification_collection.find_one({
            "user_id": user_id,
            "date": day_start,
            "statut": "depart_non_autorise"
        })
        if exists:
            return  # Notification déjà existante

        notification_doc = {
            "user_id": user_id,
            "username": username,
            "date": day_start,
            "heure": heure_depart,
            "statut": "depart_non_autorise",
            "message": f"Dernier départ hier non autorisé à {heure_depart.strftime('%H:%M:%S')}",
            "role": role,
            "adresse": adresse
        }
        notification_collection.insert_one(notification_doc)
        logging.info(f"Notification départ non autorisé créée pour user {username} hier.")
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
            (time(19, 0) <= current_time or current_time < time(5, 0))
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
                        "date_pointage": today_start
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
    {"user_id": user_id_str, "date_pointage": today_start},
    {
        "$setOnInsert": {
            "user_id": user_id_str,
            "username": user["username"],
            "date_pointage": today_start,
            "role": role
        },
        "$push": {
            "arrivees": {
                "heure": now
            }
        },
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
                            {"user_id": user_id_str, "date_pointage": today_start},
                            {
                                "$push": {
                                    "departs": {
                                        "heure": now
                                    }
                                },
                                "$set": {
                                    "adresse": adresse,
                                    "localisation": {"lat": lat, "lon": lon}
                                }
                            }
                        )

                    # Récupère les heures actuelles pour retour
                    final_doc = pointage_collection.find_one({
                        "user_id": user_id_str,
                        "date_pointage": today_start
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

# Fonction interne
def verifier_depart_non_autorise_interne(check_date=None):
    db = mongo_connection()
    if db is None:
        logging.error("Erreur base de données")
        return

    if check_date is None:
        check_date = datetime.now()

    pointage_collection = db.pointage
    notification_collection = db.notification

    day_start = datetime(check_date.year, check_date.month, check_date.day)
    day_end = datetime(check_date.year, check_date.month, check_date.day, 23, 59, 59)

    pipeline = [
        {"$match": {
            "date_pointage": {"$gte": day_start, "$lt": day_end},
            "statut": {"$in": ["depart", "depart_non_autorise"]}
        }},
        {"$sort": {"heure_pointage": -1}},
        {"$group": {
            "_id": "$user_id",
            "dernier_pointage": {"$first": "$$ROOT"}
        }}
    ]

    results = pointage_collection.aggregate(pipeline)

    for entry in results:
        pointage = entry["dernier_pointage"]
        heure_depart = pointage.get("heure_depart") or pointage.get("heure_pointage")
        if not heure_depart:
            continue

        heure_depart_time = heure_depart.time()
        is_day = time(10, 30) <= heure_depart_time <= time(17, 30)
        heure_limite = time(16, 0) if is_day else time(4, 0)

        if heure_depart_time < heure_limite:
            exists = notification_collection.find_one({
                "user_id": pointage["user_id"],
                "date": day_start,
                "statut": "depart_non_autorise"
            })
            if exists:
                continue

            notification_doc = {
                "user_id": pointage["user_id"],
                "username": pointage["username"],
                "date": day_start,
                "heure": heure_depart,
                "statut": "depart_non_autorise",
                "message": f"Dernier départ non autorisé à {heure_depart.strftime('%H:%M:%S')}",
                "role": pointage.get("role"),
                "adresse": pointage.get("adresse", "")
            }
            notification_collection.insert_one(notification_doc)

    logging.info(f"✅ Vérification des départs non autorisés pour {check_date.strftime('%Y-%m-%d')} terminée")

# ⏰ Planificateur automatique à 12h31
scheduler = BackgroundScheduler(timezone='Africa/Tunis')
scheduler.add_job(
    func=lambda: verifier_depart_non_autorise_interne(datetime.now() - timedelta(days=1)),
    trigger='cron',
    hour=6,
    minute=00,
    id='depart_non_autorise_job',
    name='Vérification départ non autorisé 12h31',
    replace_existing=True
)
scheduler.start()
logging.info("🗓️ Planificateur initialisé : vérification quotidienne à 12h31")

if __name__ == '__main__':
    app.run(debug=True, port=5010)
