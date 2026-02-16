"""Version avec détection de mouvement prolongée"""
import os, time, numpy as np, cv2, face_recognition
from typing import Dict, Any, Optional
from enum import Enum, auto
from utils.logger import setup_logger, log_presence, log_absence, log_lock, log_system, log_error
from core.locker import lock_system

class WatchState(Enum):
    UNLOCKED = auto()
    ACTIVITY_DETECTED = auto()  # Nouveau : mouvement sans reconnaissance
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
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    threshold = config["recognition_threshold"]
    lock_delay = config["lock_delay_seconds"]
    activity_grace_period = 30  # 30 secondes de grâce après dernier mouvement
    
    print(f"\n  🔍  Surveillance intelligente active")
    print(f"      • Propriétaire reconnu → système actif")
    print(f"      • Mouvement détecté → {activity_grace_period}s avant vérification")
    print(f"      • Absence totale → lock après {lock_delay}s")
    print(f"      • Intrus → lock immédiat\n")
    log_system("Surveillance démarrée")
    
    try:
        state = WatchState.UNLOCKED
        last_activity_time = time.time()  # Dernier mouvement détecté
        last_owner_recognition = time.time()  # Dernière fois que le propriétaire a été reconnu
        absence_start = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            now = time.time()
            
            # Détection légère tous les 2 frames
            if frame_count % 2 != 0:
                time.sleep(0.05)
                continue
            
            # Frame réduite pour rapidité
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Détection rapide de présence
            face_locations = face_recognition.face_locations(rgb_small, model="hog")
            
            if face_locations:
                # ═══ PRÉSENCE DÉTECTÉE ═══
                last_activity_time = now  # Mettre à jour le timer d'activité
                
                # Reconnaissance précise toutes les 15 frames (environ toutes les 3s)
                if frame_count % 15 == 0:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    full_locations = face_recognition.face_locations(rgb_frame, model="hog")
                    
                    if full_locations:
                        encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=full_locations)
                        
                        owner_found = False
                        best_dist = 999.0
                        
                        for enc in encodings:
                            dist = face_recognition.face_distance([owner_embedding], enc)[0]
                            if dist < best_dist:
                                best_dist = dist
                            if dist <= threshold:
                                owner_found = True
                                break
                        
                        if owner_found:
                            last_owner_recognition = now
                            if state != WatchState.UNLOCKED:
                                print(f"  [✅ PROPRIÉTAIRE] Reconnu (dist={best_dist:.2f})")
                                log_presence(f"Propriétaire reconnu")
                            state = WatchState.UNLOCKED
                            absence_start = None
                        
                        else:
                            # Visage détecté mais pas le propriétaire
                            time_since_last_owner = now - last_owner_recognition
                            
                            if time_since_last_owner > activity_grace_period:
                                # Trop longtemps sans reconnaissance du propriétaire
                                print(f"  [🚨 INTRUS] Visage non autorisé détecté → Lock")
                                log_absence("Intrus détecté")
                                lock_system(config.get("platform_lock", "auto"))
                                state = WatchState.LOCKED
                            else:
                                # Période de grâce : on considère que c'est juste un angle différent
                                print(f"  [👤 ACTIVITÉ] Présence détectée (vérif dans {int(activity_grace_period - time_since_last_owner)}s)")
                                state = WatchState.ACTIVITY_DETECTED
                
                else:
                    # Pas de reconnaissance cette frame, mais présence confirmée
                    if state == WatchState.ABSENCE_PENDING:
                        print(f"  [👤 MOUVEMENT] Activité détectée → annulation du lock")
                        state = WatchState.ACTIVITY_DETECTED
                    absence_start = None
            
            else:
                # ═══ AUCUNE PRÉSENCE ═══
                time_since_activity = now - last_activity_time
                
                if time_since_activity < activity_grace_period:
                    # Dans la période de grâce après activité
                    if state != WatchState.ACTIVITY_DETECTED:
                        remaining = int(activity_grace_period - time_since_activity)
                        print(f"  [⏰ GRÂCE] Dernière activité il y a {int(time_since_activity)}s (reste {remaining}s)")
                        state = WatchState.ACTIVITY_DETECTED
                
                else:
                    # Hors période de grâce → absence réelle
                    if state != WatchState.ABSENCE_PENDING:
                        state = WatchState.ABSENCE_PENDING
                        absence_start = now
                        print(f"  [⚠️  ABSENCE] Aucune activité depuis {int(time_since_activity)}s → Lock dans {lock_delay}s")
                        log_absence("Absence prolongée détectée")
                    
                    elif absence_start:
                        elapsed = now - absence_start
                        
                        if elapsed >= lock_delay:
                            print(f"\n  [🔒 LOCK] Absence confirmée → Verrouillage")
                            log_lock("Verrouillage après absence")
                            lock_system(config.get("platform_lock", "auto"))
                            state = WatchState.LOCKED
                            absence_start = None
                        else:
                            remaining = int(lock_delay - elapsed)
                            print(f"  [⏳ ATTENTE] Lock dans {remaining}s...", end="\r", flush=True)
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée\n")
        log_system("Arrêt manuel")
    finally:
        cap.release()
