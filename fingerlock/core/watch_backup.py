"""core/watch.py (simplifié)"""
import os, time, numpy as np, cv2, face_recognition
from typing import Dict, Any, Optional
from enum import Enum, auto
from utils.logger import setup_logger, log_presence, log_absence, log_lock, log_system, log_error
from core.locker import lock_system

class WatchState(Enum):
    UNLOCKED = auto()
    ABSENCE_PENDING = auto()
    LOCKED = auto()

def run_watch(config: Dict[str, Any]) -> None:
    setup_logger(config["log_path"])
    emb_path = config["embedding_path"]
    if not os.path.isfile(emb_path):
        print("\n  ❌  Aucun enrôlement trouvé !\n")
        return
    owner_embedding = np.load(emb_path)
    log_system("Embedding propriétaire chargé.")
    cap = cv2.VideoCapture(config["camera_id"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cap.isOpened():
        print("\n  ❌  Caméra non disponible.\n")
        return
    threshold = config["recognition_threshold"]
    lock_delay = config["lock_delay_seconds"]
    print(f"\n  🔍  Surveillance active (Ctrl+C pour arrêter)\n")
    log_system(f"Surveillance démarrée")
    try:
        state = WatchState.UNLOCKED
        absence_start = None
        while True:
            ret, frame = cap.read()
            if not ret: break
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            now = time.time()
            face_locations = face_recognition.face_locations(rgb_frame, model="cnn", number_of_times_to_upsample=1)
            if face_locations:
                encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                owner_found = any(face_recognition.face_distance([owner_embedding], enc)[0] <= threshold for enc in encodings)
                if owner_found:
                    if state != WatchState.UNLOCKED:
                        print("  [✅ PRESENCE]  Propriétaire reconnu")
                    state = WatchState.UNLOCKED
                    absence_start = None
                else:
                    if state == WatchState.UNLOCKED:
                        state = WatchState.ABSENCE_PENDING
                        absence_start = now
                        print(f"  [⚠️  ABSENCE]  Visage inconnu. Lock dans {lock_delay}s")
                    elif state == WatchState.ABSENCE_PENDING and absence_start and (now - absence_start) >= lock_delay:
                        print("\n  [🔒 LOCK]  Verrouillage...")
                        lock_system(config.get("platform_lock", "auto"))
                        state = WatchState.LOCKED
                        absence_start = None
            else:
                if state == WatchState.UNLOCKED:
                    state = WatchState.ABSENCE_PENDING
                    absence_start = now
                    print(f"  [⚠️  ABSENCE]  Aucun visage. Lock dans {lock_delay}s")
                elif state == WatchState.ABSENCE_PENDING and absence_start and (now - absence_start) >= lock_delay:
                    print("\n  [🔒 LOCK]  Verrouillage...")
                    lock_system(config.get("platform_lock", "auto"))
                    state = WatchState.LOCKED
                    absence_start = None
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n  🛑  Arrêté\n")
    finally:
        cap.release()
