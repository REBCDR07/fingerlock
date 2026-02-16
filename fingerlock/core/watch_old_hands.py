"""Détection de mains pour garder le système actif"""
import os, time, cv2
from typing import Dict, Any
from utils.logger import setup_logger, log_lock, log_system
from core.locker import lock_system

try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_NEW = True
except:
    import mediapipe as mp
    MEDIAPIPE_NEW = False

def run_watch(config: Dict[str, Any]) -> None:
    setup_logger(config["log_path"])
    
    cap = cv2.VideoCapture(config["camera_id"])
    if not cap.isOpened():
        print("\n  ❌  Caméra non disponible.\n")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    lock_delay = config.get("lock_delay_seconds", 5)
    
    print(f"\n  ✋ Surveillance par détection de MAINS")
    print(f"      • Main visible → système actif")
    print(f"      • Pas de main pendant {lock_delay}s → 🔒 lock")
    print(f"      • Ctrl+C pour arrêter\n")
    
    log_system("Surveillance mains démarrée")
    
    # Initialiser MediaPipe Hands
    if MEDIAPIPE_NEW:
        print("  ⚠️  MediaPipe nouvelle version détectée")
        print("      Cette version nécessite des modèles supplémentaires")
        print("      Utilisez plutôt : pip install mediapipe==0.10.0\n")
        cap.release()
        return
    else:
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    try:
        last_hand_time = time.time()
        locked = False
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            now = time.time()
            
            # Traiter toutes les frames (détection main est rapide)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                # Main(s) détectée(s)
                num_hands = len(results.multi_hand_landmarks)
                last_hand_time = now
                
                print(f"  [✋ ACTIF] {num_hands} main(s) détectée(s)     ", end="\r")
                
                if locked:
                    print(f"\n  [🔓 UNLOCK] Main détectée → système réactivé")
                    log_system("Système déverrouillé (main détectée)")
                    locked = False
            
            else:
                # Aucune main détectée
                absence = now - last_hand_time
                
                if absence >= lock_delay and not locked:
                    print(f"\n  [🔒 LOCK] Aucune main depuis {int(absence)}s → Verrouillage")
                    log_lock(f"Verrouillage après {int(absence)}s sans main")
                    lock_system(config.get("platform_lock", "auto"))
                    locked = True
                
                elif absence < lock_delay:
                    remaining = int(lock_delay - absence)
                    print(f"  [⏳] Pas de main : {int(absence)}s / {lock_delay}s (lock dans {remaining}s)     ", end="\r")
            
            time.sleep(0.05)  # ~20 FPS, très fluide
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée\n")
        log_system("Arrêt manuel")
    finally:
        hands.close()
        cap.release()

