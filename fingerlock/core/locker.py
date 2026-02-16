"""
core/locker.py
--------------
Module de verrouillage système cross-plateforme.

Détection automatique du système d'exploitation et exécution
de la commande de verrouillage appropriée.

| Plateforme | Commande utilisée                                        |
|------------|----------------------------------------------------------|
| Windows    | rundll32 user32.dll,LockWorkStation                      |
| macOS      | osascript -e 'activate "System Events"' + lock           |
| Linux      | xdg-open ou screenlock / xlock / gnome-screensaver-activate |

Pour Linux, plusieurs backends sont testés dans l'ordre de priorité.
"""

import subprocess
import platform
import sys
from typing import Optional

from fingerlock.utils.logger import log_lock, log_error


# ---------------------------------------------------------------------------
# Commandes par plateforme
# ---------------------------------------------------------------------------
_LOCK_COMMANDS = {
    "windows": [
        ["rundll32", "user32.dll,LockWorkStation"],
    ],
    "macos": [
        # Méthode 1 : raccourci clavier Ctrl+Option+Cmd (le plus fiable)
        [
            "osascript", "-e",
            'tell application "System Events" to key down {control, option, command} & key up {control, option, command}'
        ],
        # Méthode 2 : activer le screensaver (fallback, nécessite Accessibilité)
        [
            "osascript", "-e",
            'tell application "System Events" to activate application "ScreenSaverEngine"'
        ],
    ],
    "linux": [
        # Ordre de priorité par fréquence d'usage.
        # xdg-open n'a PAS d'option --lock → volontairement absent.
        ["gnome-screensaver-command", "-l"],              # GNOME (le plus commun)
        ["xscreensaver-command", "-activate"],       # xscreensaver (X11 générique)
        ["kde-open5", "--lock"],                     # KDE / Plasma
        ["i3lock"],                                  # i3wm
        ["swaylock"],                                # sway (Wayland)
        ["hyprlock"],                                # Hyprland
        ["xlock", "-mode", "blank"],                 # xlock (dernier recours)
    ],
}


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------
def lock_system(platform_override: str = "auto") -> bool:
    """
    Verrouille le système.
    Retourne True si la commande a été lancée avec succès.

    Args:
        platform_override: "auto" | "windows" | "macos" | "linux"
    """
    os_name = _resolve_platform(platform_override)

    if os_name not in _LOCK_COMMANDS:
        log_error(f"Plateforme non supportée : {os_name}")
        print(f"\n  ❌  Plateforme '{os_name}' non supportée pour le verrouillage.")
        return False

    log_lock(f"Tentative de verrouillage – plateforme={os_name}")

    for cmd in _LOCK_COMMANDS[os_name]:
        if _try_lock(cmd):
            log_lock(f"Verrouillage réussi avec : {' '.join(cmd)}")
            print(f"  🔒  Système verrouillé. Commande : {' '.join(cmd)}")
            return True

    # Aucune commande ne fonctionne
    log_error("Aucune commande de verrouillage ne fonctionnait sur cette plateforme.")
    print("\n  ❌  Verrouillage échoué – aucune commande disponible.")
    print("      Linux : installez l'une des options : gnome-screensaver, xscreensaver, i3lock, swaylock.")
    return False


def get_lock_info() -> str:
    """Retourne une chaîne descriptive de la plateforme détectée."""
    system = platform.system()
    if system == "Windows":
        return "Windows (rundll32 LockWorkStation)"
    elif system == "Darwin":
        return "macOS (osascript)"
    elif system == "Linux":
        return "Linux (multi-backend : gnome-screensaver / xscreensaver / i3lock / swaylock)"
    return f"Inconnu ({system})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_platform(override: str) -> str:
    """Résout la plateforme cible."""
    if override != "auto":
        return override
    system = platform.system()
    mapping = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}
    return mapping.get(system, system.lower())


def _try_lock(cmd: list) -> bool:
    """
    Tente d'exécuter une commande de verrouillage.
    Retourne True si la commande a été lancée sans erreur.
    """
    try:
        # check=False : on ne veut pas lever une exception si returncode != 0
        # timeout=5 : éviter les blocages infinis
        result = subprocess.run(
            cmd,
            timeout=5,
            capture_output=True,
            text=True,
        )
        # Pour Windows et macOS, returncode 0 = succès
        # Pour Linux, certains backends retournent != 0 mais fonctionnent quand même
        return result.returncode == 0

    except FileNotFoundError:
        # La commande n'existe pas sur ce système
        return False
    except subprocess.TimeoutExpired:
        # Commande bloquée → considérer comme lancée (ex: xlock)
        return True
    except Exception as e:
        log_error(f"Erreur lors du verrouillage avec {cmd} : {e}")
        return False
