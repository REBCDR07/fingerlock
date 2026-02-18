"""FingerLock – Surveillance avec evdev (compatible Wayland)"""
import time, select, glob
from typing import Dict, Any
from fingerlock.utils.logger import setup_logger, log_lock, log_system
from fingerlock.core.lockscreen import show_lockscreen

try:
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False


class ActivityMonitor:
    def __init__(self):
        self.last_activity = time.time()
        self.running = True
        self.event_count = 0
        self.devices = []
        
        if EVDEV_AVAILABLE:
            # Trouver tous les devices input
            for path in glob.glob('/dev/input/event*'):
                try:
                    dev = InputDevice(path)
                    # Garder uniquement clavier et souris
                    caps = dev.capabilities()
                    if ecodes.EV_KEY in caps or ecodes.EV_REL in caps:
                        self.devices.append(dev)
                except:
                    pass
            print(f"  📡 {len(self.devices)} périphériques détectés")

    def update(self):
        """Vérifie les events sur tous les devices"""
        if not self.devices:
            return
        
        # Polling non-bloquant
        r, w, x = select.select(self.devices, [], [], 0)
        for dev in r:
            try:
                for event in dev.read():
                    if event.type in (ecodes.EV_KEY, ecodes.EV_REL):
                        self.last_activity = time.time()
                        self.event_count += 1
            except:
                pass


def run_watch(config: Dict[str, Any]) -> None:
    setup_logger(config["log_path"])

    lock_delay   = config.get("lock_delay_seconds", 10)
    pattern_hash = config.get("pattern_hash")

    if not EVDEV_AVAILABLE:
        print("\n  ❌ Module 'evdev' manquant !")
        print("  Installez-le : pipx runpip fingerlock install evdev\n")
        return

    print(f"\n  ⌨️  Surveillance active (evdev)")
    print(f"  ⏱️  Verrouillage après {lock_delay}s d'inactivité")
    print(f"  🔐 Déverrouillage par schéma plein écran")
    print(f"  Ctrl+C pour arrêter\n")
    log_system("Surveillance démarrée")

    monitor = ActivityMonitor()
    
    if not monitor.devices:
        print("  ❌ Aucun périphérique input accessible !")
        print("  Vérifiez que vous êtes dans le groupe 'input'")
        return

    try:
        locked = False
        last_debug = 0

        while True:
            now = time.time()
            
            # Mettre à jour les events
            monitor.update()
            
            inactivity = now - monitor.last_activity

            # Debug toutes les 3s
            if now - last_debug >= 3:
                print(f"  [DEBUG] Events détectés: {monitor.event_count}")
                last_debug = now

            if inactivity >= lock_delay and not locked:
                print(f"\n  [🔒 LOCK] {int(inactivity)}s d'inactivité")
                log_lock(f"Verrouillage après {int(inactivity)}s")
                locked = True

                unlocked = show_lockscreen(pattern_hash)

                if unlocked:
                    print("\n  [🔓 UNLOCK] Déverrouillé ✅")
                    log_system("Système déverrouillé")
                    locked = False
                    monitor.last_activity = time.time()
                    monitor.event_count = 0
                else:
                    print("  ❌ Trop de tentatives — arrêt")
                    log_system("Arrêt après trop de tentatives")
                    break

            elif inactivity < lock_delay:
                remaining = int(lock_delay - inactivity)
                print(f"  [✅ ACTIF] {int(inactivity)}s (lock dans {remaining}s) | Events: {monitor.event_count}     ", end="\r")

            time.sleep(0.1)  # Poll plus fréquent

    except KeyboardInterrupt:
        print("\n\n  🛑  Arrêté\n")
        log_system("Arrêt manuel")
    except Exception as e:
        print(f"\n  ❌ Erreur: {e}\n")
    finally:
        for dev in monitor.devices:
            try:
                dev.close()
            except:
                pass
