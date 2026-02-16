"""
core/enroll.py (version simplifiée sans MediaPipe)
"""
import os
import numpy as np
import cv2
import face_recognition
from typing import Dict, Any, List, Optional

from utils.logger import setup_logger, log_enroll, log_error, log_system


def run_enrollment(camera_id: int, output_path: str, config: Dict[str, Any]) -> None:
    setup_logger(config["log_path"])
    
    print("\n  ── Phase d'enrôlement ──\n")
    log_enroll("Démarrage de l'enrôlement du propriétaire.")
    
    if os.path.isfile(output_path):
        print(f"  ⚠️  Un enrôlement existe déjà : {output_path}")
        resp = input("      Surcharger ? (o/N) : ").strip().lower()
        if resp not in ("o", "oui", "y", "yes"):
            print("  → Enrôlement annulé.\n")
            return
        log_enroll("Surcharge de l'enrôlement précédent confirmée.")
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        log_error(f"Impossible d'ouvrir la caméra index={camera_id}")
        print(f"\n  ❌  Caméra index {camera_id} non disponible.\n")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    capture_count = config.get("capture_count", 30)
    embeddings: List[np.ndarray] = []
    
    print(f"  📸  Regardez directement la caméra.")
    print(f"      Nous allons capturer {capture_count} frames de votre visage.\n")
    
    frame_idx = 0
    max_wait_frames = 300
    
    while len(embeddings) < capture_count:
        ret, frame = cap.read()
        if not ret:
            log_error("Échec de la lecture d'une frame caméra.")
            break
        
        frame_idx += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Détection directe avec face_recognition
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        if face_locations:
            encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=[face_locations[0]])
            if encodings:
                embeddings.append(encodings[0])
                progress = len(embeddings) / capture_count * 100
                print(f"\r  📸  Capture : [{int(progress):>3}%] {len(embeddings)}/{capture_count} frames", end="", flush=True)
                frame_idx = 0
        else:
            if frame_idx > max_wait_frames:
                print("\n\n  ⏱️  Timeout : aucun visage détecté depuis 10 secondes.\n")
                log_enroll("Timeout pendant l'enrôlement – aucun visage détecté.")
                cap.release()
                return
    
    cap.release()
    
    if len(embeddings) < capture_count:
        print(f"\n\n  ❌  Enrôlement incomplet : {len(embeddings)}/{capture_count} frames captées.\n")
        return
    
    print("\n")
    mean_embedding = np.mean(embeddings, axis=0)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    np.save(output_path, mean_embedding)
    
    log_enroll(f"Enrôlement réussi. Embedding sauvegardé → {output_path}")
    print(f"  ✅  Enrôlement terminé avec succès !")
    print(f"      Embedding sauvegardé : {output_path}")
    print(f"      Lancez `python main.py watch` pour démarrer la surveillance.\n")
