from flask import Flask, jsonify
from flask_cors import CORS
from flask import request
import cv2
import face_recognition
import pyttsx3
import numpy as np
import io
from PIL import Image
from pymongo import MongoClient
from bson.binary import Binary
import logging
from datetime import datetime, date
import requests

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

def mongo_connection():
    try:
        client = MongoClient("mongodb+srv://stage:stage@cluster0.gbm1c.mongodb.net/stage?retryWrites=true&w=majority")
        db = client.get_database("stage")
        logging.info("Connexion à MongoDB réussie")
        return db
    except Exception as e:
        logging.error(f"Erreur de connexion à MongoDB: {e}")
        return None

def load_known_faces():
    db = mongo_connection()
    if db is None:
        return [], [], {}, {}

    known_faces = []
    known_names = []
    known_emails = {}
    known_user_ids = {}

    try:
        users = db.user.find({"photo": {"$exists": True}})
        for user in users:
            try:
                image_data = user.get('photo')
                if not image_data:
                    continue

                if isinstance(image_data, Binary):
                    image_bytes = bytes(image_data)
                else:
                    image_bytes = image_data

                img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                img_np = np.array(img)

                face_locations = face_recognition.face_locations(img_np)
                encodings = face_recognition.face_encodings(img_np, face_locations)
                if not encodings:
                    logging.warning(f"Pas de visage détecté pour user {user.get('username', '?')}")
                    continue

                encoding = encodings[0]
                username = user.get("username", "Inconnu")

                known_faces.append(encoding)
                known_names.append(username)
                known_emails[username] = user.get("email", "")
                known_user_ids[username] = str(user.get("_id", ""))
            except Exception as e:
                logging.error(f"Erreur image utilisateur {user.get('_id', '?')}: {e}")
                continue
    except Exception as e:
        logging.error(f"Erreur MongoDB: {e}")

    logging.info(f"Visages chargés : {len(known_faces)}")
    logging.info(f"Noms : {known_names}")
    return known_faces, known_names, known_emails, known_user_ids

# Charger les visages au démarrage
known_faces, known_names, known_emails, known_user_ids = load_known_faces()

def detect_faces(frame):
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb_small_frame)
    encodings = face_recognition.face_encodings(rgb_small_frame, locations)
    return locations, encodings

def recognize_person(encoding):
    matches = face_recognition.compare_faces(known_faces, encoding)
    if True in matches:
        index = matches.index(True)
        return {
            "username": known_names[index]
        }
    return None

def reverse_geocode(lat, lon):
    try:
        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 18,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'mon-app-pointage/1.0'}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('display_name', 'Adresse inconnue')
        else:
            return 'Erreur géocodage'
    except Exception as e:
        logging.error(f"Erreur géocodage inverse: {e}")
        return 'Erreur géocodage'

@app.route('/analytics')
def index():
    return "Welcome"

@app.route('/get_person_data', methods=['POST'])
def get_person_data():
    video_capture = None
    engine = None
    try:
        # Récupérer JSON envoyé par le client
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')
        if lat is None or lon is None:
            return jsonify({"message": "Coordonnées GPS manquantes"}), 400

        db = mongo_connection()
        if db is None:
            return jsonify({"message": "Erreur base de données"}), 500
        pointage_collection = db.pointage

        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            return jsonify({"message": "Erreur caméra"}), 500

        engine = pyttsx3.init()

        ret, frame = video_capture.read()
        if not ret:
            return jsonify({"message": "Erreur capture image"}), 500

        locations, encodings = detect_faces(frame)
        if not encodings:
            engine.say("You must sign up.")
            engine.runAndWait()
            return jsonify({"message": "Inconnu"}), 404

        for encoding in encodings:
            user = recognize_person(encoding)
            if user:
                user_id = known_user_ids[user["username"]]
                today = date.today()
                existing_pointages = list(pointage_collection.find({
                    "user_id": user_id,
                    "date_pointage": {"$eq": datetime(today.year, today.month, today.day)}
                }).sort("heure_pointage"))

                statut = "arrivee" if not existing_pointages else \
                         ("depart" if existing_pointages[-1].get("statut") == "arrivee" else "arrivee")

                localisation = {"lat": lat, "lon": lon}
                adresse = reverse_geocode(lat, lon)

                pointage_doc = {
                    "user_id": user_id,
                    "username": user["username"],
                    "date_pointage": datetime(today.year, today.month, today.day),
                    "heure_pointage": datetime.now(),
                    "statut": statut,
                    "localisation": localisation,
                    "adresse": adresse
                }
                pointage_collection.insert_one(pointage_doc)

                engine.say(f"Welcome, {user['username']}. Statut {statut}")
                engine.runAndWait()
                return jsonify({"username": user["username"], "statut": statut, "adresse": adresse}), 200

        engine.say("You must sign up.")
        engine.runAndWait()
        return jsonify({"message": "Inconnu"}), 404

    except Exception as e:
        logging.error(f"Erreur reconnaissance : {e}")
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        if video_capture:
            video_capture.release()
        if engine:
            engine.stop()

if __name__ == '__main__':
    app.run(debug=True, port=5010)
