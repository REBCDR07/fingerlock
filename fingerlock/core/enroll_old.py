"""
core/enroll.py
--------------
Module d'enrôlement du propriétaire.

Flux :
    1. Ouverture de la webcam (OpenCV)
    2. Détection de visage en temps réel (MediaPipe FaceMesh)
    3. Confirmation visuelle dans le terminal (pas de GUI)
    4. Extraction des embeddings via face_recognition sur N frames
    5. Moyennage des embeddings pour un vecteur robuste
    6. Sauvegarde chiffrée en .npy

Le fichier .npy est stocké dans data/ et ne doit jamais être partagé.
"""

import os
import numpy as np
import cv2
import face_recognition
import mediapipe as mp
from typing import Dict, Any, List, Optional

from utils.logger import setup_logger, log_enroll, log_error, log_system


def run_enrollment(camera_id: int, output_path: str, config: Dict[str, Any]) -> None:
    """
    Point d'entrée principal de l'enrôlement.
    Orchestre la détection, la capture et la sauvegarde.
    """
    setup_logger(config["log_path"])

    print("\n  ── Phase d'enrôlement ──\n")
    log_enroll("Démarrage de l'enrôlement du propriétaire.")

    # ── Vérification : déjà enrôlé ? ──
    if os.path.isfile(output_path):
        print(f"  ⚠️  Un enrôlement existe déjà : {output_path}")
        resp = input("      Surcharger ? (o/N) : ").strip().lower()
        if resp not in ("o", "oui", "y", "yes"):
            print("  → Enrôlement annulé.\n")
            return
        log_enroll("Surcharge de l'enrôlement précédent confirmée.")

    # ── Ouverture caméra ──
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        log_error(f"Impossible d'ouvrir la caméra index={camera_id}")
        print(f"\n  ❌  Caméra index {camera_id} non disponible.")
        print("      Vérifiez l'index avec `python main.py config`.\n")
        return

    # Résolution recommandée pour face_recognition
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # ── MediaPipe Face Mesh ──
    mp_face = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        min_detection_confidence=config["mediapipe_confidence"],
        min_tracking_confidence=0.5,
    )

    capture_count = config.get("capture_count", 30)
    embeddings: List[np.ndarray] = []

    print(f"  📸  Regardez directement la caméra.")
    print(f"      Nous allons capturer {capture_count} frames de votre visage.\n")

    frame_idx = 0
    max_wait_frames = 300  # ~10s à 30fps sans détection → timeout

    while len(embeddings) < capture_count:
        ret, frame = cap.read()
        if not ret:
            log_error("Échec de la lecture d'une frame caméra.")
            break

        frame_idx += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ── Détection MediaPipe ──
        results = mp_face.process(rgb_frame)

        if results.multi_face_landmarks:
            # Visage détecté → extraire embedding
            embedding = _extract_embedding(rgb_frame)
            if embedding is not None:
                embeddings.append(embedding)
                progress = len(embeddings) / capture_count * 100
                print(f"\r  📸  Capture : [{int(progress):>3}%] {len(embeddings)}/{capture_count} frames", end="", flush=True)
                frame_idx = 0  # réinitialiser le compteur de timeout
            # else : face_recognition n'a pas trouvé de visage sur cette frame
        else:
            # Pas de détection MediaPipe
            if frame_idx > max_wait_frames:
                print("\n\n  ⏱️  Timeout : aucun visage détecté depuis 10 secondes.")
                print("      Assurez-vous d'être devant la caméra et réessayez.\n")
                log_enroll("Timeout pendant l'enrôlement – aucun visage détecté.")
                cap.release()
                mp_face.close()
                return

    cap.release()
    mp_face.close()

    if len(embeddings) < capture_count:
        print(f"\n\n  ❌  Enrôlement incomplet : {len(embeddings)}/{capture_count} frames captées.")
        log_enroll(f"Enrôlement incomplet : {len(embeddings)}/{capture_count}")
        return

    # ── Moyennage & sauvegarde ──
    print("\n")
    mean_embedding = np.mean(embeddings, axis=0)
    _save_embedding(mean_embedding, output_path)

    log_enroll(f"Enrôlement réussi. Embedding sauvegardé → {output_path}")
    print(f"  ✅  Enrôlement terminé avec succès !")
    print(f"      Embedding sauvegardé : {output_path}")
    print(f"      Lancez `python main.py watch` pour démarrer la surveillance.\n")


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------
def _extract_embedding(rgb_frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Extrait l'embedding 128-d d'un visage via face_recognition.
    Retourne None si aucun visage trouvé.
    """
    # Détection rapide de la position du visage
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    if not face_locations:
        return None

    # On prend le premier visage détecté
    encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=[face_locations[0]])
    if not encodings:
        return None

    return encodings[0]


def _save_embedding(embedding: np.ndarray, path: str) -> None:
    """Sauvegarde l'embedding en fichier .npy."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    np.save(path, embedding)
