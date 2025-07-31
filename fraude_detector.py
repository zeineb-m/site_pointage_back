from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import os
from datetime import datetime
from pymongo import MongoClient
from bson.binary import Binary
import uuid
from insightface.app import FaceAnalysis
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === Initialisation InsightFace Anti-Spoofing
face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

# === Connexion MongoDB
def mongo_connection():
    try:
        client = MongoClient(
            "mongodb+srv://stage:stage@cluster0.gbm1c.mongodb.net/stage?retryWrites=true&w=majority"
        )
        return client["stage"]
    except Exception as e:
        logging.error(f"Erreur connexion MongoDB : {e}")
        return None

def detect_antispoof(frame):
    raisons = []
    fraude = False

    faces = face_app.get(frame)
    if not faces:
        raisons.append("Aucun visage détecté pour analyse liveness")
        return True, raisons

    seuil_liveness = 0.7

    for i, face in enumerate(faces):
        # Récupérer la bbox du visage (x1,y1,x2,y2)
        bbox = face.bbox  # c’est un ndarray [x1, y1, x2, y2]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        # Seuil arbitraire pour visage trop grand = pas un téléphone, donc pas fraude webcam
        taille_visage_seuil = 200  # à ajuster selon test, en pixels

        if height > taille_visage_seuil or width > taille_visage_seuil:
            # Visage trop grand, on suppose webcam : ne pas détecter fraude liveness ici
            logging.info(f"Visage #{i+1} trop grand ({width:.0f}x{height:.0f}), supposé webcam, pas de fraude liveness")
            return False, []  # On renvoie pas de fraude dans ce cas

        score_kps = face.get('kps_score', None)
        score_global = face.get('score', 1.0)
        score = score_kps if score_kps is not None else score_global

        if score < seuil_liveness:
            fraude = True
            raisons.append(f"Visage #{i+1} : score liveness faible ({score:.2f})")

    return fraude, raisons

def detect_telephone_screen(frame):
    logging.info("🔎 Détection téléphone écran démarrée")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    logging.info(f"Contours détectés : {len(contours)}")

    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = h / float(w) if w != 0 else 0
        area = cv2.contourArea(cnt)
        logging.debug(f"Contour {i}: x={x}, y={y}, w={w}, h={h}, aspect_ratio={aspect_ratio:.2f}, area={area}")
         # Dessiner rectangle autour du contour pour debug
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        if 1.3 < aspect_ratio < 3.5 and 2000 < area < 50000:
             logging.warning(f"📱 Téléphone détecté ! aspect_ratio={aspect_ratio:.2f}, aire={area}")
             cv2.imwrite("debug_telephone_detected.jpg", frame)
             logging.info("Image debug_telephone_detected.jpg sauvegardée pour inspection")

             return True

    logging.info("📱 Aucun objet téléphone détecté")
    return False

def detect_screen_recording(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False, ["Impossible d'ouvrir la vidéo"]

    edge_count = moire_count = reflect_count = frame_count = 0
    raisons = []

    total_frames_to_check = 150
    frame_total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_sampling_step = max(1, int(frame_total / total_frames_to_check)) if frame_total > 0 else 1

    def compute_moire_score(gray):
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        mag = np.abs(fshift)
        magnitude_spectrum = np.log(mag + 1)

        rows, cols = magnitude_spectrum.shape
        crow, ccol = rows // 2, cols // 2
        mask = np.zeros_like(magnitude_spectrum)

        radius_inner = 30
        radius_outer = 80

        y, x = np.ogrid[:rows, :cols]
        dist_from_center = np.sqrt((y - crow)**2 + (x - ccol)**2)
        mask[(dist_from_center > radius_inner) & (dist_from_center < radius_outer)] = 1

        moire_energy = np.sum(magnitude_spectrum * mask) / np.sum(mask)
        return moire_energy

    total_checked_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_sampling_step != 0:
            continue

        total_checked_frames += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        border = 50
        top = np.mean(edges[:border, :])
        bottom = np.mean(edges[-border:, :])
        left = np.mean(edges[:, :border])
        right = np.mean(edges[:, -border:])
        border_density = np.mean([top, bottom, left, right])
        if border_density > 15:
            edge_count += 1

        moire_score = compute_moire_score(gray)
        logging.debug(f"Frame {frame_count}: moiré score = {moire_score:.2f}")
        if moire_score > 12.0:
            moire_count += 1

        brightness = np.percentile(frame, 99)
        if 245 < brightness < 255:
            reflect_count += 1

        if total_checked_frames >= total_frames_to_check:
            break

    cap.release()

    edge_ratio = edge_count / total_checked_frames if total_checked_frames else 0
    moire_ratio = moire_count / total_checked_frames if total_checked_frames else 0
    reflect_ratio = reflect_count / total_checked_frames if total_checked_frames else 0

    logging.debug(f"Ratios détectés - Edge: {edge_ratio:.2f}, Moiré: {moire_ratio:.2f}, Reflet: {reflect_ratio:.2f}")

    seuil_frame_ratio = 0.55

    if total_checked_frames < 30:
        logging.info("Vidéo trop courte, aucune fraude détectée.")
        return False, []

    if edge_ratio > seuil_frame_ratio:
        raisons.append("Contours élevés en bordure d'image (probable capture d'écran)")
    if moire_ratio > seuil_frame_ratio:
        raisons.append("Motifs moiré détectés (filmage d'écran)")
    if reflect_ratio > seuil_frame_ratio and reflect_count > 15:
        raisons.append("Luminosité anormale détectée (reflet de l'écran)")

    return (len(raisons) > 0), raisons

def save_video_to_mongo(db, video_path, username):
    try:
        with open(video_path, 'rb') as f:
            video_data = f.read()

        doc = {
            "username": username,
            "video": Binary(video_data),
            "date": datetime.now(),
            "fraude": True,
            "nom_fichier": os.path.basename(video_path)
        }
        db.videos_fraude.insert_one(doc)
        logging.info(f"Vidéo sauvegardée pour {username}")
    except Exception as e:
        logging.error(f"Erreur sauvegarde vidéo MongoDB: {e}")

@app.route('/detect_fraude', methods=['POST'])
def detect_fraude():
    logging.info("🔍 Début traitement detect_fraude")
    fraude = False
    raisons = []
    filepath = None

    try:
        if 'video' not in request.files:
            return jsonify({"error": "Fichier vidéo manquant"}), 400

        video_file = request.files['video']
        username = request.form.get("username", "").strip()

        if not username:
            return jsonify({"error": "Nom d'utilisateur requis"}), 400

        filename = f"{uuid.uuid4().hex}.avi"
        os.makedirs("temp_videos", exist_ok=True)
        filepath = os.path.join("temp_videos", filename)
        video_file.save(filepath)

        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()

        if duration > 15:
            os.remove(filepath)
            return jsonify({"error": "Durée de la vidéo > 15s"}), 400

        db = mongo_connection()
        if db is None:
            os.remove(filepath)
            return jsonify({"error": "Erreur base de données"}), 500

        user_exists = db.user.find_one({"username": username})
        if not user_exists:
            os.remove(filepath)
            return jsonify({"fraude": False, "message": "Utilisateur inconnu"}), 200

        # 📱 Lecture de la première frame pour détection visage et heuristique écran
        cap = cv2.VideoCapture(filepath)
        ret, first_frame = cap.read()
        cap.release()

        if not ret or first_frame is None:
            os.remove(filepath)
            return jsonify({"error": "Impossible de lire la première frame"}), 400

        # === Analyse taille du visage ===
        faces = face_app.get(first_frame)
        visage_grand = False
        taille_seuil = 200  # seuil en pixels à ajuster selon test

        if faces:
            for face in faces:
                bbox = face.bbox  # bbox = [x1, y1, x2, y2]
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                if height > taille_seuil or width > taille_seuil:
                    visage_grand = True
                    logging.info(f"Visage détecté grand ({width}x{height}), supposé webcam")
                    break
        else:
            logging.info("Aucun visage détecté sur la première frame")

        # 📼 Détection heuristique écran (reflets, luminosité, etc.)
        fraude_heuristique, raisons_heuristique = detect_screen_recording(filepath)

        # Si visage grand, on ignore les alertes heuristiques écran
        if visage_grand:
            logging.info("Visage grand détecté : on ignore les alertes heuristiques écran")
            raisons_heuristique = []
            fraude_heuristique = False

        # 📱 Vérifier les 20 premières frames pour détecter un téléphone
        cap = cv2.VideoCapture(filepath)
        frame_index = 0
        frame_detected = None
        while frame_index < 20:
            ret, frame = cap.read()
            if not ret:
                break
            frame_index += 1
            if detect_telephone_screen(frame):
                logging.info("📱 Téléphone détecté - fraude forcée pour la démo")
                raisons_heuristique.append("Objet rectangulaire vertical lumineux détecté (suspicion téléphone)")
                fraude_heuristique = True
                frame_detected = frame
                break
        cap.release()

        # 🧠 Analyse insightface sur la frame détectée ou première frame
        if frame_detected is None:
            frame = first_frame
            ret = True
        else:
            frame = frame_detected
            ret = frame is not None

        if ret:
            fraude_insight, raisons_insight = detect_antispoof(frame)

            # 📝 Compilation des raisons
            if fraude_heuristique:
                raisons += [f"Analyse écran : {r}" for r in raisons_heuristique]
            if fraude_insight:
                raisons += [f"Analyse liveness : {r}" for r in raisons_insight]

            # 🎯 Filtrage des fausses alertes (tu peux ajuster)
            raisons_sérieuses = [
                r for r in raisons
                if "liveness" in r.lower() or "téléphone" in r.lower() or "objet rectangulaire" in r.lower()
            ]

            # 💡 Logique de détection finale
            fraude = fraude_heuristique or fraude_insight
            if fraude:
                save_video_to_mongo(db, filepath, username)
                    # Préparation mail
                sujet = "🚨 Alerte fraude détectée"
                contenu = (
                f"Une fraude a été détectée pour l'utilisateur : {username} \n"
                f"Date et heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Raisons :\n - " + "\n - ".join(raisons)
                )
                envoyer_mail_rh(sujet, contenu)
        else:
            raisons = ["Impossible de lire la frame analysée"]

        os.remove(filepath)

        return jsonify({
            "fraude": fraude,
            "raisons": raisons
        }), 200

    except Exception as e:
        logging.error(f"❌ Erreur dans detect_fraude : {e}", exc_info=True)
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500
def envoyer_mail_rh(sujet, contenu):
    db = mongo_connection()
    if db is None:
        logging.error("Impossible de se connecter à la BD pour récupérer les emails RH")
        return

    # Récupérer les emails des RH
    rh_users = db.user.find({"role": "HR"})
    rh_emails = [user["email"] for user in rh_users if "email" in user]

    if not rh_emails:
        logging.warning("Aucun email RH trouvé pour notification.")
        return

    expediteur = "neflahela@gmail.com"  # A remplacer par ton email
    mot_de_passe = "irbl gbvn ksdc hmkw"  # A remplacer par ton mot de passe d'app

    for destinataire in rh_emails:
        msg = MIMEMultipart()
        msg['From'] = expediteur
        msg['To'] = destinataire
        msg['Subject'] = sujet
        msg.attach(MIMEText(contenu, 'plain'))

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as serveur:
                serveur.starttls()
                serveur.login(expediteur, mot_de_passe)
                serveur.send_message(msg)
                logging.info(f"Mail envoyé à {destinataire}")
        except Exception as e:
            logging.error(f"Erreur envoi mail à {destinataire}: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
