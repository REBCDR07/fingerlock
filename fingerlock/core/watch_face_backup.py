"""Version simple et efficace"""
import os, time, numpy as np, cv2, face_recognition
from typing import Dict, Any
from utils.logger import setup_logger, log_presence, log_absence, log_lock, log_system
from core.locker import lock_system

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
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    threshold = config["recognition_threshold"]
    lock_delay = config["lock_delay_seconds"]
    
    print(f"\n  🔍  Surveillance active")
    print(f"      Délai absence : {lock_delay}s | Ctrl+C pour arrêter\n")
    
    try:
        last_face_time = time.time()  # Dernier moment où un visage a été vu
        locked = False
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            now = time.time()
            
            # Analyse 1 frame sur 3 pour rapidité
            if frame_count % 3 != 0:
                time.sleep(0.05)
                continue
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Détection rapide
            face_locations = face_recognition.face_locations(rgb_frame, model="cnn")
            
            if face_locations:
                # Visage détecté → mettre à jour le timer
                last_face_time = now
                
                # Reconnaissance toutes les 10 frames
                if frame_count % 10 == 0:
                    encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
                    
                    owner_found = False
                    for enc in encodings:
                        dist = face_recognition.face_distance([owner_embedding], enc)[0]
                        if dist <= threshold:
                            owner_found = True
                            print(f"  [✅ OK] Propriétaire (dist={dist:.2f})", end="\r")
                            break
                    
                    if not owner_found:
                        print(f"  [👤 PRÉSENCE] Activité détectée", end="\r")
                
                if locked:
                    print("\n  [🔓 UNLOCK] Présence détectée → système actif")
                    locked = False
            
            else:
                # Aucun visage
                time_without_face = now - last_face_time
                
                if time_without_face >= lock_delay and not locked:
                    print(f"\n  [🔒 LOCK] Absence de {int(time_without_face)}s → Verrouillage")
                    log_lock("Verrouillage après absence")
                    lock_system(config.get("platform_lock", "auto"))
                    locked = True
                
                elif time_without_face < lock_delay:
                    remaining = int(lock_delay - time_without_face)
                    print(f"  [⏳] Pas de visage depuis {int(time_without_face)}s (lock dans {remaining}s)", end="\r")
            
            time.sleep(0.15)
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Arrêté\n")
    finally:
        cap.release()
