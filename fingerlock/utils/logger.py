"""
utils/logger.py
---------------
Journalisation centralisée pour FaceLock.

Chaque événement est enregistré avec :
    - Horodatage ISO 8601
    - Niveau (INFO / WARNING / ERROR)
    - Catégorie : PRESENCE | ABSENCE | LOCK | SYSTEM | ENROLL
    - Message détaillé

Format fichier :
    2025-06-15T10:30:45 | INFO     | PRESENCE | Visage propriétaire reconnu (dist=0.42)

Format console :
    [10:30:45] ✅ PRESENCE  Visage propriétaire reconnu (dist=0.42)
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Instance unique du logger
# ---------------------------------------------------------------------------
_logger: Optional[logging.Logger] = None


def setup_logger(log_path: str) -> logging.Logger:
    """
    Configure et retourne le logger singleton.
    À appeler une seule fois au démarrage.
    """
    global _logger

    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)

    logger = logging.getLogger("facelock")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # éviter les doublons si appelé plusieurs fois

    # ── Handler fichier ──
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_fmt)
    logger.addHandler(fh)

    # ── Handler console (couleurs basiques via préfixes) ──
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("  %(message)s"))
    logger.addHandler(ch)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Retourne le logger déjà configuré (ou un logger par défaut)."""
    if _logger is None:
        # Fallback si setup n'a pas été appelé
        fallback = logging.getLogger("facelock")
        fallback.addHandler(logging.StreamHandler(sys.stdout))
        fallback.setLevel(logging.INFO)
        return fallback
    return _logger


# ---------------------------------------------------------------------------
# Fonctions de log structuré par catégorie
# ---------------------------------------------------------------------------
_ICONS = {
    "PRESENCE": "✅",
    "ABSENCE": "⚠️ ",
    "LOCK":     "🔒",
    "SYSTEM":   "ℹ️ ",
    "ENROLL":   "📸",
    "ERROR":    "❌",
}


def _format_msg(category: str, message: str) -> str:
    icon = _ICONS.get(category, "  ")
    return f"[{datetime.now().strftime('%H:%M:%S')}] {icon} {category:<10} {message}"


def log_presence(message: str) -> None:
    get_logger().info(_format_msg("PRESENCE", message))


def log_absence(message: str) -> None:
    get_logger().warning(_format_msg("ABSENCE", message))


def log_lock(message: str) -> None:
    get_logger().warning(_format_msg("LOCK", message))


def log_system(message: str) -> None:
    get_logger().info(_format_msg("SYSTEM", message))


def log_enroll(message: str) -> None:
    get_logger().info(_format_msg("ENROLL", message))


def log_error(message: str) -> None:
    get_logger().error(_format_msg("ERROR", message))


# ---------------------------------------------------------------------------
# Affichage des derniers logs (commande `logs`)
# ---------------------------------------------------------------------------
def tail_logs(log_path: str, lines: int = 30) -> None:
    """Affiche les N dernières lignes du fichier de log."""
    if not os.path.isfile(log_path):
        print(f"\n  ⚠️  Aucun fichier de log trouvé : {log_path}")
        print("      Lancez d'abord `python main.py enroll` ou `python main.py watch`.\n")
        return

    with open(log_path, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    recent = all_lines[-lines:] if len(all_lines) > lines else all_lines

    print(f"\n  ── Dernières {lines} entrées de log ──\n")
    for line in recent:
        print(f"    {line.rstrip()}")
    print()
