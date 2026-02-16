"""Détection d'activité clavier/souris + caméra"""
import time, threading
from typing import Dict, Any
from pynput import mouse, keyboard
from fingerlock.utils.logger import setup_logger, log_lock, log_system
from fingerlock.core.locker import lock_system

class ActivityMonitor:
    def __init__(self):
        self.last_activity = time.time()
        self.running = True
    
    def on_move(self, x, y):
        self.last_activity = time.time()
    
    def on_click(self, x, y, button, pressed):
        self.last_activity = time.time()
    
    def on_key(self, key):
        self.last_activity = time.time()

def run_watch(config: Dict[str, Any]) -> None:
    setup_logger(config["log_path"])
    
    lock_delay = config.get("lock_delay_seconds", 5)
    
    print(f"\n  ⌨️  Surveillance CLAVIER + SOURIS")
    print(f"      • Activité détectée → système actif ✅")
    print(f"      • Inactivité {lock_delay}s → 🔒 lock automatique")
    print(f"      • Ctrl+C pour arrêter\n")
    
    log_system("Surveillance inputs démarrée")
    
    monitor = ActivityMonitor()
    
    # Démarrer les listeners
    mouse_listener = mouse.Listener(
        on_move=monitor.on_move,
        on_click=monitor.on_click
    )
    keyboard_listener = keyboard.Listener(
        on_press=monitor.on_key
    )
    
    mouse_listener.start()
    keyboard_listener.start()
    
    try:
        locked = False
        
        while monitor.running:
            now = time.time()
            inactivity = now - monitor.last_activity
            
            if inactivity >= lock_delay and not locked:
                print(f"\n  [🔒 LOCK] Inactivité de {int(inactivity)}s → Verrouillage")
                log_lock(f"Verrouillage après {int(inactivity)}s d'inactivité")
                lock_system(config.get("platform_lock", "auto"))
                locked = True
            
            elif inactivity < lock_delay:
                if locked:
                    print(f"\n  [🔓 UNLOCK] Activité détectée → système réactivé")
                    log_system("Système déverrouillé")
                    locked = False
                
                remaining = int(lock_delay - inactivity)
                print(f"  [✅ ACTIF] Dernière activité : {int(inactivity)}s (lock dans {remaining}s)     ", end="\r")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée\n")
        log_system("Arrêt manuel")
        monitor.running = False
    finally:
        mouse_listener.stop()
        keyboard_listener.stop()

