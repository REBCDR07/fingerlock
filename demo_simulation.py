#!/usr/bin/env python3
"""
demo_simulation.py
------------------
Démonstration simulée de FaceLock SANS webcam ni face_recognition.

Ce script illustre le fonctionnement complet en mode simulation :
1. Simule l'enrôlement (génère un embedding fictif)
2. Simule la surveillance avec scénarios prédéfinis
3. Affiche les logs et états en temps réel

Usage :
    python demo_simulation.py
"""

import sys
import os
import time
import random
import numpy as np

# Ajouter le projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import load_config
from utils.logger import setup_logger, log_enroll, log_presence, log_absence, log_lock, log_system


def simulate_enrollment():
    """Simule l'enrôlement en créant un embedding aléatoire."""
    print("\n" + "="*60)
    print("  📸  SIMULATION : ENRÔLEMENT")
    print("="*60 + "\n")
    
    config = load_config()
    setup_logger(config["log_path"])
    
    log_enroll("Démarrage de l'enrôlement simulé.")
    print("  Simulation de capture de 30 frames...")
    
    # Simuler la capture progressive
    for i in range(1, 31):
        progress = int((i / 30) * 100)
        print(f"\r  📸  Capture : [{progress:>3}%] {i}/30 frames", end="", flush=True)
        time.sleep(0.05)
    
    # Créer un embedding fictif (128 dimensions comme face_recognition)
    fake_embedding = np.random.randn(128).astype(np.float64)
    
    # Sauvegarder
    emb_path = config["embedding_path"]
    os.makedirs(os.path.dirname(emb_path), exist_ok=True)
    np.save(emb_path, fake_embedding)
    
    print("\n")
    log_enroll(f"Enrôlement simulé réussi. Embedding sauvegardé → {emb_path}")
    print(f"  ✅  Enrôlement simulé terminé !")
    print(f"      Embedding (128-d) sauvegardé : {emb_path}\n")


def simulate_watch():
    """Simule la surveillance avec différents scénarios."""
    print("\n" + "="*60)
    print("  🔍  SIMULATION : SURVEILLANCE")
    print("="*60 + "\n")
    
    config = load_config()
    setup_logger(config["log_path"])
    
    # Vérifier l'embedding
    emb_path = config["embedding_path"]
    if not os.path.isfile(emb_path):
        print("  ❌  Aucun enrôlement trouvé ! Lancez d'abord : python demo_simulation.py\n")
        return
    
    owner_embedding = np.load(emb_path)
    log_system(f"Embedding propriétaire chargé (shape={owner_embedding.shape}).")
    
    threshold = config["recognition_threshold"]
    lock_delay = config["lock_delay_seconds"]
    
    print(f"  🔍  Surveillance simulée active.")
    print(f"      Seuil de reconnaissance : {threshold}")
    print(f"      Délai avant verrouillage : {lock_delay}s")
    print(f"      Appuyez Ctrl+C pour arrêter.\n")
    
    log_system(f"Surveillance simulée démarrée – threshold={threshold}, delay={lock_delay}s")
    
    # Scénarios de simulation
    scenarios = [
        ("proprietaire", 10, "Propriétaire présent et reconnu"),
        ("absence", 3, "Propriétaire s'éloigne"),
        ("lock_countdown", lock_delay, "Décompte avant verrouillage"),
        ("locked", 2, "Système verrouillé"),
        ("proprietaire", 5, "Propriétaire revient"),
        ("intrus", 4, "Visage non reconnu détecté"),
        ("lock_countdown", lock_delay, "Décompte après intrusion"),
        ("locked", 2, "Système verrouillé"),
    ]
    
    try:
        for scenario_type, duration, description in scenarios:
            print(f"\n  ── Scénario : {description} ({duration}s) ──")
            
            if scenario_type == "proprietaire":
                for i in range(duration):
                    # Distance simulée (proche du seuil mais valide)
                    dist = random.uniform(0.35, threshold - 0.05)
                    log_presence(f"Propriétaire présent (dist={dist:.3f})")
                    print(f"  [✅ PRESENCE]  Propriétaire reconnu (dist={dist:.3f})")
                    time.sleep(1)
            
            elif scenario_type == "absence":
                log_absence("Aucun visage détecté – décompte verrouillage.")
                print(f"  [⚠️  ABSENCE]  Aucun visage. Verrouillage dans {lock_delay}s...")
                time.sleep(duration)
            
            elif scenario_type == "intrus":
                log_absence("Visage non reconnu détecté – décompte verrouillage.")
                print(f"  [⚠️  ABSENCE]  Visage inconnu détecté. Verrouillage dans {lock_delay}s...")
                time.sleep(duration)
            
            elif scenario_type == "lock_countdown":
                for i in range(duration):
                    remaining = duration - i
                    print(f"  [⏳ WAIT]     Verrouillage dans {remaining}s...", end="\r", flush=True)
                    time.sleep(1)
                print()  # nouvelle ligne
            
            elif scenario_type == "locked":
                log_lock("Délai écoulé – verrouillage simulé du système.")
                print(f"  [🔒 LOCK]      Verrouillage du système (simulation)")
                log_lock("Système verrouillé avec succès (simulation).")
                print(f"  [🔒 LOCK]      Système verrouillé. Surveillance continue en arrière-plan.")
                time.sleep(duration)
        
        print("\n  ✅  Simulation terminée avec succès.\n")
        log_system("Simulation de surveillance terminée.")
        
    except KeyboardInterrupt:
        print("\n\n  🛑  Surveillance arrêtée par l'utilisateur.\n")
        log_system("Surveillance simulée arrêtée manuellement (Ctrl+C).")


def show_logs():
    """Affiche les logs générés."""
    print("\n" + "="*60)
    print("  📋  LOGS GÉNÉRÉS")
    print("="*60 + "\n")
    
    config = load_config()
    log_path = config["log_path"]
    
    if not os.path.isfile(log_path):
        print(f"  ⚠️  Aucun fichier de log trouvé : {log_path}\n")
        return
    
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    recent = lines[-20:] if len(lines) > 20 else lines
    
    print(f"  Dernières {len(recent)} entrées de log :\n")
    for line in recent:
        print(f"    {line.rstrip()}")
    print()


def main():
    print("\n" + "="*60)
    print("  🔒 FaceLock – DÉMONSTRATION SIMULÉE")
    print("="*60)
    print("\n  Cette démo simule le fonctionnement complet de FaceLock")
    print("  SANS nécessiter de webcam ni de bibliothèque face_recognition.\n")
    
    print("  1️⃣  Enrôlement simulé (génère embedding fictif)")
    print("  2️⃣  Surveillance simulée (scénarios prédéfinis)")
    print("  3️⃣  Afficher les logs générés")
    print("  4️⃣  Quitter\n")
    
    while True:
        choice = input("  Votre choix (1-4) : ").strip()
        
        if choice == "1":
            simulate_enrollment()
            input("\n  Appuyez sur Entrée pour continuer...")
        
        elif choice == "2":
            simulate_watch()
            input("\n  Appuyez sur Entrée pour continuer...")
        
        elif choice == "3":
            show_logs()
            input("\n  Appuyez sur Entrée pour continuer...")
        
        elif choice == "4":
            print("\n  👋  Au revoir !\n")
            break
        
        else:
            print("  ⚠️  Choix invalide. Essayez 1, 2, 3 ou 4.\n")


if __name__ == "__main__":
    main()
