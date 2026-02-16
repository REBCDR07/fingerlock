"""Détection de mains avec MediaPipe nouvelle API"""
import os, time, cv2, numpy as np
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
    
    print(f"\n  ✋ Surveillance par détection de MAINS")
    print(f"      • Main visible → système actif")
    print(f"      • Pas de main pendant {lock_delay}s → 🔒 lock")
    print(f"      • Ctrl+C pour arrêter\n")
    
    log_system("Surveillance mains démarrée")
    
    # Télécharger le modèle s'il n'existe pas
    model_path = "/tmp/hand_landmarker.task"
    if not os.path.exists(model_path):
        print("  📥 Téléchargement du modèle de détection de mains...")
        import urllib.request
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        try:
            urllib.request.urlretrieve(url, model_path)
            print("  ✅ Modèle téléchargé\n")
        except Exception as e:
            print(f"  ❌ Erreur téléchargement: {e}")
            print("  💡 Solution alternative : détection de mouvement simple\n")
            cap.release()
            return
    
    # Initialiser MediaPipe Hands (nouvelle API)
    try:
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5
        )
        detector = vision.HandLandmarker.create_from_options(options)
    except Exception as e:
        print(f"  ❌ Erreur initialisation MediaPipe: {e}")
        print("  💡 Basculement vers détection de mouvement...\n")
        cap.release()
        _run_motion_detection(config)
        return
    
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
            
            # Convertir en format MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = vision.Image(image_format=vision.ImageFormat.SRGB, data=rgb_frame)
            
            # Détection
            detection_result = detector.detect(mp_image)
            
            if detection_result.hand_landmarks:
                # Main(s) détectée(s)
                num_hands = len(detection_result.hand_landmarks)
                last_hand_time = now
                
                print(f"  [✋ ACTIF] {num_hands} main(s) détectée(s)     ", end="\r")
                
                if locked:
                    print(f"\n  [🔓 UNLOCK] Main détectée → système réactivé")
                    log_system("Système déverrouillé")
                    locked = False
            
            else:
                # Aucune main
                absence = now - last_hand_time
                
                if absence >= lock_delay and not locked:
                    print(f"\n  [🔒 LOCK] Aucune main depuis {int(absence)}s → Verrouillage")
                    log_lock(f"Verrouillage après {int(absence)}s")
                    lock_system(config.get("platform_lock", "auto"))
                    locked = True
                
                elif absence < lock_delay:
                    remaining = int(lock_delay - absence)
                    print(f"  [⏳] Pas de main : {int(absence)}s/{lock_delay}s (lock dans {remaining}s)     ", end="\r")
            
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée\n")
        log_system("Arrêt manuel")
    finally:
        cap.release()


def _run_motion_detection(config: Dict[str, Any]) -> None:
    """Fallback : détection de mouvement simple"""
    cap = cv2.VideoCapture(config["camera_id"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    lock_delay = config.get("lock_delay_seconds", 5)
    
    print(f"  🎥 Mode DÉTECTION DE MOUVEMENT")
    print(f"      • Mouvement détecté → système actif")
    print(f"      • Immobilité {lock_delay}s → 🔒 lock\n")
    
    try:
        prev_frame = None
        last_motion_time = time.time()
        locked = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            now = time.time()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is None:
                prev_frame = gray
                continue
            
            # Différence entre frames
            frame_diff = cv2.absdiff(prev_frame, gray)
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            motion_pixels = cv2.countNonZero(thresh)
            
            # Seuil de mouvement (ajustable)
            if motion_pixels > 500:
                last_motion_time = now
                print(f"  [🎯 MOUVEMENT] Activité détectée ({motion_pixels} pixels)     ", end="\r")
                if locked:
                    print(f"\n  [🔓] Mouvement → système actif")
                    locked = False
            else:
                absence = now - last_motion_time
                if absence >= lock_delay and not locked:
                    print(f"\n  [🔒 LOCK] {int(absence)}s d'immobilité → Verrouillage")
                    lock_system(config.get("platform_lock", "auto"))
                    locked = True
                elif absence < lock_delay:
                    print(f"  [⏳] Immobile : {int(absence)}s/{lock_delay}s     ", end="\r")
            
            prev_frame = gray
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Arrêté\n")
    finally:
        cap.release()

