"""
core/watch.py
-------------
Module de surveillance en temps réel.

Boucle principale :
    1. Lecture continue de la webcam (OpenCV)
    2. Détection de visage (MediaPipe FaceMesh) – rapide, CPU-friendly
    3. Si visage détecté → extraction embedding (face_recognition)
    4. Comparaison avec l'embedding du propriétaire
    5. Gestion de l'état machine : UNLOCKED ↔ ABSENCE_PENDING → LOCKED

Diagramme d'état :
    ┌──────────┐  visage propriétaire   ┌───────────┐
    │ UNLOCKED │ ◄─────────────────── │   WATCH   │
    └──────────┘                        └───────────┘
         │                                    ▲
         │ absence détectée                   │ visage propriétaire
         ▼                                    │   (avant timeout)
    ┌──────────────────┐                      │
    │ ABSENCE_PENDING  │ ─── timeout ───────► │
    └──────────────────┘                      │
                                              │
                                    ┌─────────┘
                                    │ LOCKED (lock lancé)
                                    └─────────────────────
"""

import os
import time
import numpy as np
import cv2
import face_recognition
import mediapipe as mp
from typing import Dict, Any, Optional
from enum import Enum, auto

from utils.logger import setup_logger, log_presence, log_absence, log_lock, log_system, log_error
from core.locker import lock_system


# ---------------------------------------------------------------------------
# États de la machine à états
# ---------------------------------------------------------------------------
class WatchState(Enum):
    UNLOCKED = auto()          # Propriétaire présent et reconnu
    ABSENCE_PENDING = auto()   # Visage disparati – décompte en cours
    LOCKED = auto()            # Système verrouillé


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
def run_watch(config: Dict[str, Any]) -> None:
    """
    Lance la boucle de surveillance principale.
    Bloque jusqu'à Ctrl+C.
    """
    setup_logger(config["log_path"])

    # ── Vérification préalable : embeddings existants ? ──
    emb_path = config["embedding_path"]
    if not os.path.isfile(emb_path):
        print("\n  ❌  Aucun enrôlement trouvé !")
        print(f"      Fichier attendu : {emb_path}")
        print("      Lancez d'abord : python main.py enroll\n")
        return

    owner_embedding = np.load(emb_path)
    log_system("Embedding propriétaire chargé.")

    # ── Ouverture caméra ──
    cap = cv2.VideoCapture(config["camera_id"])
    if not cap.isOpened():
        log_error(f"Caméra index={config['camera_id']} indisponible.")
        print(f"\n  ❌  Caméra index {config['camera_id']} non disponible.\n")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # ── MediaPipe ──
    mp_face = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=2,   # détecte jusqu'à 2 visages pour repérer les intrus
        min_detection_confidence=config["mediapipe_confidence"],
        min_tracking_confidence=0.5,
    )

    # ── Paramètres ──
    threshold = config["recognition_threshold"]
    lock_delay = config["lock_delay_seconds"]

    # ── État machine ──
    state = WatchState.UNLOCKED
    absence_start: Optional[float] = None

    print("\n  🔍  Surveillance active.")
    print(f"      Seuil de reconnaissance : {threshold}")
    print(f"      Délai avant verrouillage : {lock_delay}s")
    print(f"      Appuyez Ctrl+C pour arrêter.\n")

    log_system(f"Surveillance démarrée – threshold={threshold}, delay={lock_delay}s")

    try:
        _watch_loop(cap, mp_face, owner_embedding, threshold, lock_delay, config)
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée par l'utilisateur.\n")
        log_system("Surveillance arrêtée manuellement (Ctrl+C).")
    finally:
        cap.release()
        mp_face.close()


# ---------------------------------------------------------------------------
# Boucle principale (séparée pour clarté)
# ---------------------------------------------------------------------------
def _watch_loop(
    cap: cv2.VideoCapture,
    mp_face,
    owner_embedding: np.ndarray,
    threshold: float,
    lock_delay: int,
    config: Dict[str, Any],
) -> None:
    """Boucle de surveillance – tourne indéfiniment."""

    state = WatchState.UNLOCKED
    absence_start: Optional[float] = None

    # Deux compteurs séparés pour éviter qu'ils se bloquent mutuellement (BUG 3)
    last_presence_log: float = 0      # log périodique "propriétaire présent"
    last_countdown_print: float = 0   # affichage du décompte "Xs restantes"

    log_interval: float = 3.0         # log presence toutes les 3s en régime stable

    # Compteur de frames sans détection consécutives pour filtrer les glitches
    no_face_streak = 0
    NO_FACE_STREAK_THRESHOLD = 15     # ~0.5s à 15fps avant de considérer l'absence

    while True:
        ret, frame = cap.read()
        if not ret:
            log_error("Interruption du flux caméra.")
            print("  ❌  Flux caméra perdu. Vérifiez la connexion.\n")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        now = time.time()

        # ── Détection MediaPipe ──
        results = mp_face.process(rgb_frame)
        faces_detected = (
            results.multi_face_landmarks is not None
            and len(results.multi_face_landmarks) > 0
        )

        # ============================================================
        # VISAGE(S) DÉTECTÉ(S)
        # ============================================================
        if faces_detected:
            no_face_streak = 0
            owner_found, _intruder_found, best_dist = _identify_faces(
                rgb_frame, owner_embedding, threshold
            )

            if owner_found:
                # ── PROPRIÉTAIRE RECONNU ──
                # Transition depuis n'importe quel état vers UNLOCKED
                if state != WatchState.UNLOCKED:
                    log_presence(f"Propriétaire reconnu à nouveau (dist={best_dist:.3f})")
                    print(f"\n  [✅ PRESENCE]  Propriétaire reconnu (dist={best_dist:.3f})")

                state = WatchState.UNLOCKED
                absence_start = None

                # Log périodique en régime stable (compteur indépendant)
                if now - last_presence_log >= log_interval:
                    log_presence(f"Propriétaire présent (dist={best_dist:.3f})")
                    last_presence_log = now

            else:
                # ── VISAGE NON RECONNU (intrus potentiel) ──
                if state == WatchState.UNLOCKED:
                    state = WatchState.ABSENCE_PENDING
                    absence_start = now
                    log_absence("Visage non reconnu détecté – décompte verrouillage.")
                    print(f"  [⚠️  ABSENCE]  Visage inconnu détecté. Verrouillage dans {lock_delay}s...")

                elif state == WatchState.ABSENCE_PENDING and absence_start is not None:
                    elapsed = now - absence_start
                    if elapsed >= lock_delay:
                        state, absence_start = _do_lock(config)
                    elif now - last_countdown_print >= 1.0:
                        remaining = lock_delay - elapsed
                        print(f"  [⏳ WAIT]     Verrouillage dans {remaining:.0f}s...", end="\r")
                        last_countdown_print = now

                # État LOCKED + visage intrus → on reste verrouillé, on ne fait rien

        # ============================================================
        # AUCUN VISAGE DÉTECTÉ
        # ============================================================
        else:
            no_face_streak += 1

            if no_face_streak >= NO_FACE_STREAK_THRESHOLD:
                # Absence confirmée (pas un glitch caméra)

                if state == WatchState.UNLOCKED:
                    state = WatchState.ABSENCE_PENDING
                    absence_start = now
                    log_absence("Aucun visage détecté – décompte verrouillage.")
                    print(f"  [⚠️  ABSENCE]  Aucun visage. Verrouillage dans {lock_delay}s...")

                elif state == WatchState.ABSENCE_PENDING and absence_start is not None:
                    elapsed = now - absence_start
                    if elapsed >= lock_delay:
                        state, absence_start = _do_lock(config)
                    elif now - last_countdown_print >= 1.0:
                        remaining = lock_delay - elapsed
                        print(f"  [⏳ WAIT]     Verrouillage dans {remaining:.0f}s...", end="\r")
                        last_countdown_print = now

                # État LOCKED + pas de visage → on reste verrouillé, rien à faire

        # Petit délai pour ne pas surcharger le CPU (target ~15 fps)
        time.sleep(0.067)


# ---------------------------------------------------------------------------
# Identification des visages sur une frame
# ---------------------------------------------------------------------------
def _identify_faces(
    rgb_frame: np.ndarray,
    owner_embedding: np.ndarray,
    threshold: float,
) -> tuple:
    """
    Analyse les visages sur la frame.

    Returns:
        (owner_found: bool, intruder_found: bool, best_distance: float)
    """
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    if not face_locations:
        return False, False, 999.0

    encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)

    owner_found = False
    intruder_found = False
    best_dist = 999.0

    for enc in encodings:
        dist = face_recognition.face_distance([owner_embedding], enc)[0]
        if dist < best_dist:
            best_dist = dist

        if dist <= threshold:
            owner_found = True
        else:
            intruder_found = True

    return owner_found, intruder_found, best_dist


# ---------------------------------------------------------------------------
# Helpers d'état
# ---------------------------------------------------------------------------
def _handle_absence(state, now, absence_start, lock_delay, config, reason=""):
    """Placeholder pour future extension (notifications, alertes, …)."""
    pass


def _do_lock(config: Dict[str, Any]) -> tuple:
    """
    Exécute le verrouillage et retourne le nouvel état.
    """
    log_lock("Délai écoulé – verrouillage du système.")
    print(f"\n  [🔒 LOCK]      Verrouillage du système…")

    success = lock_system(config.get("platform_lock", "auto"))

    if success:
        log_lock("Système verrouillé avec succès.")
        print(f"  [🔒 LOCK]      Système verrouillé. Surveillance continue en arrière-plan.\n")
    else:
        log_lock("Échec du verrouillage – surveillance continue.")
        print(f"  [❌ LOCK ERR]  Échec du verrouillage. Vérifiez la config `platform_lock`.\n")

    return WatchState.LOCKED, None
