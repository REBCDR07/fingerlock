"""Détection de MOUVEMENT simple et efficace"""
import cv2, time
from typing import Dict, Any
from utils.logger import setup_logger, log_lock, log_system
from core.locker import lock_system

def run_watch(config: Dict[str, Any]) -> None:
    setup_logger(config["log_path"])
    
    cap = cv2.VideoCapture(config["camera_id"])
    if not cap.isOpened():
        print("\n  ❌  Caméra non disponible.\n")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    lock_delay = config.get("lock_delay_seconds", 5)
    
    print(f"\n  🎥 Surveillance par DÉTECTION DE MOUVEMENT")
    print(f"      • Mouvement détecté → système actif ✅")
    print(f"      • Immobilité {lock_delay}s → 🔒 lock")
    print(f"      • Portée : tout le champ de la caméra")
    print(f"      • Ctrl+C pour arrêter\n")
    
    log_system("Surveillance mouvement démarrée")
    
    try:
        prev_frame = None
        last_motion_time = time.time()
        locked = False
        motion_threshold = 800  # Sensibilité (plus bas = plus sensible)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            now = time.time()
            
            # Conversion en niveaux de gris et flou pour stabilité
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is None:
                prev_frame = gray
                time.sleep(0.1)
                continue
            
            # Calcul de la différence entre frames
            frame_diff = cv2.absdiff(prev_frame, gray)
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            motion_pixels = cv2.countNonZero(thresh)
            
            if motion_pixels > motion_threshold:
                # Mouvement détecté
                last_motion_time = now
                intensity = "🔥" if motion_pixels > 5000 else "🎯"
                print(f"  [{intensity} ACTIF] Mouvement détecté ({motion_pixels} px)          ", end="\r")
                
                if locked:
                    print(f"\n  [🔓 UNLOCK] Mouvement → système réactivé")
                    log_system("Système déverrouillé (mouvement détecté)")
                    locked = False
            
            else:
                # Pas de mouvement significatif
                absence = now - last_motion_time
                
                if absence >= lock_delay and not locked:
                    print(f"\n  [🔒 LOCK] Immobilité de {int(absence)}s → Verrouillage")
                    log_lock(f"Verrouillage après {int(absence)}s d'immobilité")
                    lock_system(config.get("platform_lock", "auto"))
                    locked = True
                
                elif absence < lock_delay:
                    remaining = int(lock_delay - absence)
                    print(f"  [⏳ VEILLE] Immobile depuis {int(absence)}s (lock dans {remaining}s)          ", end="\r")
            
            prev_frame = gray
            time.sleep(0.1)  # ~10 FPS
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée\n")
        log_system("Arrêt manuel")
    finally:
        cap.release()

