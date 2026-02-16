"""Version hybride : détection rapide + reconnaissance précise"""
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
    if not cap.isOpened():
        print("\n  ❌  Caméra non disponible.\n")
        return
    
    # Résolution HD pour meilleure détection à distance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    threshold = config["recognition_threshold"]
    lock_delay = config["lock_delay_seconds"]
    
    print(f"\n  🔍  Surveillance active (Ctrl+C pour arrêter)")
    print(f"      Portée : ~1.5m | Délai absence : {lock_delay}s\n")
    log_system("Surveillance démarrée")
    
    try:
        state = WatchState.UNLOCKED
        absence_start = None
        last_check_time = 0
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            now = time.time()
            
            # Détection rapide tous les 3 frames (pour fluidité)
            if frame_count % 3 != 0:
                time.sleep(0.05)
                continue
            
            # Réduire la taille pour accélérer
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Détection rapide (HOG)
            face_locations = face_recognition.face_locations(rgb_small, model="hog")
            
            if face_locations:
                # Mouvement détecté → réinitialiser le timer d'absence
                if state == WatchState.ABSENCE_PENDING:
                    print("  [👤 MOUVEMENT] Présence détectée, vérification...")
                
                # Reconnaissance précise toutes les 10 frames seulement
                if frame_count % 10 == 0:
                    # Utiliser la frame originale pour reconnaissance
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    full_locations = face_recognition.face_locations(rgb_frame, model="hog")
                    
                    if full_locations:
                        encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=full_locations)
                        
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
                        
                        if owner_found:
                            if state != WatchState.UNLOCKED:
                                print(f"  [✅ PROPRIÉTAIRE] Reconnu (dist={best_dist:.2f})")
                                log_presence(f"Propriétaire reconnu (dist={best_dist:.2f})")
                            state = WatchState.UNLOCKED
                            absence_start = None
                        
                        elif intruder_found:
                            print(f"  [🚨 INTRUS] Visage non autorisé ! Lock immédiat")
                            log_absence("Intrus détecté")
                            lock_system(config.get("platform_lock", "auto"))
                            state = WatchState.LOCKED
                            absence_start = None
                
                else:
                    # Pas de reconnaissance, mais présence détectée
                    # → garder le système actif (pas de lock)
                    if state == WatchState.UNLOCKED:
                        pass  # Tout va bien
                    elif state == WatchState.ABSENCE_PENDING:
                        # Réinitialiser car il y a du mouvement
                        absence_start = now
            
            else:
                # Aucun visage détecté
                if state == WatchState.UNLOCKED:
                    state = WatchState.ABSENCE_PENDING
                    absence_start = now
                    print(f"  [⚠️  ABSENCE] Aucune présence. Lock dans {lock_delay}s")
                    log_absence("Absence détectée")
                
                elif state == WatchState.ABSENCE_PENDING and absence_start:
                    elapsed = now - absence_start
                    remaining = lock_delay - elapsed
                    
                    if elapsed >= lock_delay:
                        print(f"\n  [🔒 LOCK] Absence confirmée → Verrouillage")
                        log_lock("Verrouillage après absence")
                        lock_system(config.get("platform_lock", "auto"))
                        state = WatchState.LOCKED
                        absence_start = None
                    
                    elif now - last_check_time >= 1.0:
                        print(f"  [⏳ ATTENTE] Lock dans {int(remaining)}s...", end="\r", flush=True)
                        last_check_time = now
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée\n")
        log_system("Arrêt manuel")
    finally:
        cap.release()
