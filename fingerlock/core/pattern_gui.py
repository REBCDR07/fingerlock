"""Setup du schéma via le lock screen plein écran"""
from fingerlock.core.lockscreen import draw_pattern_screen
import hashlib
from typing import List
from pathlib import Path


def _hash(pattern: List[int]) -> str:
    return hashlib.sha256(
        "-".join(str(p) for p in pattern).encode()).hexdigest()


def setup_pattern_gui(config_dir: Path) -> dict:
    print("\n  🔐 Configuration du schéma...")
    print("  L'écran va passer en mode plein écran.\n")

    while True:
        # Étape 1 : dessiner
        print("  Étape 1/2 : Dessinez votre schéma")
        first = draw_pattern_screen("Dessinez votre schéma")
        if not first or len(first) < 3:
            print("  ❌ Schéma trop court, recommencez.\n")
            continue

        code = "".join(str(p) for p in first)
        print(f"  ✅ Schéma : {code}\n")

        # Étape 2 : confirmer
        print("  Étape 2/2 : Confirmez votre schéma")
        confirm = draw_pattern_screen("Confirmez votre schéma")
        if not confirm:
            continue

        if first == confirm:
            print(f"  ✅ Schéma confirmé : {code}\n")
            break
        else:
            print("  ❌ Schémas différents, recommencez.\n")

    # Délai
    while True:
        try:
            raw   = input("  ⏱️  Délai avant verrouillage (secondes) [10] : ").strip()
            delay = int(raw) if raw else 10
            if delay >= 1:
                break
            print("  ❌ Minimum 1 seconde\n")
        except ValueError:
            print("  ❌ Entrez un nombre entier\n")

    print(f"\n  ✅ FingerLock configuré ! Délai : {delay}s\n")

    return {
        "pattern_hash":       _hash(first),
        "pattern_code":       code,   # stocké en clair pour debug
        "lock_delay_seconds": delay,
        "platform_lock":      "auto",
        "log_path":           str(config_dir / "fingerlock.log"),
    }


def verify_pattern_gui(stored_hash: str) -> bool:
    from fingerlock.core.lockscreen import show_lockscreen
    return show_lockscreen(stored_hash)
