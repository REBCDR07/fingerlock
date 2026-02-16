#!/usr/bin/env python3
"""
FingerLock – Application de sécurité par reconnaissance de doigts.
Point d'entrée CLI principal.

Usages :
    python main.py enroll                     # Enrôlement du propriétaire
    python main.py watch                      # Surveillance en temps réel
    python main.py watch --threshold 0.55     # Avec seuil personnalisé
    python main.py status                     # État du système
    python main.py logs                       # Afficher les derniers logs
    python main.py config                     # Afficher la config actuelle
"""

import argparse
import sys
import os

# ---------------------------------------------------------------------------
# Ajout du répertoire parent au PATH pour les imports relatifs
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import load_config, save_config, print_config
from core.enroll import run_enrollment
from core.watch import run_watch
from core.locker import get_lock_info
from utils.logger import setup_logger, tail_logs

# ---------------------------------------------------------------------------
# Banner ASCII
# ---------------------------------------------------------------------------
BANNER = r"""
 _____ _                       _                _    
|  ___(_)_ __   __ _  ___ _ __| |    ___   ___| | __
| |_  | | '_ \ / _` |/ _ \ '__| |   / _ \ / __| |/ /
|  _| | | | | | (_| |  __/ |  | |__| (_) | (__|   < 
|_|   |_|_| |_|\__, |\___|_|  |_____\___/ \___|_|\_\
               |___/                                 
        Sécurité par Reconnaissance de Doigts
        ======================================
"""


# ---------------------------------------------------------------------------
# Sous-commandes
# ---------------------------------------------------------------------------
def cmd_enroll(args, config):
    """Enrôle le visage du propriétaire via la webcam."""
    run_enrollment(
        camera_id=args.camera if args.camera is not None else config["camera_id"],
        output_path=config["embedding_path"],
        config=config,
    )


def cmd_watch(args, config):
    """Lance la surveillance en temps réel."""
    # CLI override sur la config chargée
    if args.threshold is not None:
        config["recognition_threshold"] = args.threshold
    if args.delay is not None:
        config["lock_delay_seconds"] = args.delay
    if args.camera is not None:
        config["camera_id"] = args.camera

    run_watch(config)


def cmd_status(args, config):
    """Affiche l'état actuel du système."""
    import os
    from utils.logger import get_logger

    logger = get_logger()
    emb_path = config["embedding_path"]

    print("\n" + BANNER)
    print("  ── État du système ──")
    print(f"  Embeddings propriétaire : {'✅  Présents' if os.path.isfile(emb_path) else '❌  Non enrôlé'}")
    print(f"  Fichier embeddings      : {emb_path}")
    print(f"  Caméra utilisée         : index {config['camera_id']}")
    print(f"  Seuil de confiance      : {config['recognition_threshold']}")
    print(f"  Délai avant verrouillage: {config['lock_delay_seconds']} s")
    print(f"  Plateforme de lock      : {get_lock_info()}")
    print()


def cmd_logs(args, config):
    """Affiche les derniers logs."""
    tail_logs(config["log_path"], lines=args.lines)


def cmd_config(args, config):
    """Affiche la configuration en cours."""
    print("\n  ── Configuration actuelle ──\n")
    print_config(config)
    print()


# ---------------------------------------------------------------------------
# Parser CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="facelock",
        description="🔒 FingerLock – Sécurité par reconnaissance de doigts",
        epilog="Exemple : python main.py enroll   →   python main.py watch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", help="Commande à exécuter")
    sub.required = True

    # ── enroll ──
    p_enroll = sub.add_parser("enroll", help="Enrôler le visage du propriétaire")
    p_enroll.add_argument("-c", "--camera", type=int, default=None, help="Index de la caméra (par défaut : config)")

    # ── watch ──
    p_watch = sub.add_parser("watch", help="Surveillance temps réel + auto-verrouillage")
    p_watch.add_argument("-t", "--threshold", type=float, default=None, help="Seuil de reconnaissance (0.0–1.0)")
    p_watch.add_argument("-d", "--delay", type=int, default=None, help="Délai (s) avant verrouillage après absence")
    p_watch.add_argument("-c", "--camera", type=int, default=None, help="Index de la caméra")

    # ── status ──
    sub.add_parser("status", help="Afficher l'état du système")

    # ── logs ──
    p_logs = sub.add_parser("logs", help="Afficher les derniers logs")
    p_logs.add_argument("-n", "--lines", type=int, default=30, help="Nombre de lignes à afficher")

    # ── config ──
    sub.add_parser("config", help="Afficher la configuration actuelle")

    return parser


# ---------------------------------------------------------------------------
# Entrée principale
# ---------------------------------------------------------------------------
def main():
    parser = build_parser()
    args = parser.parse_args()

    # Charger la config depuis le fichier YAML
    config = load_config()

    # Mapper commande → fonction
    commands = {
        "enroll": cmd_enroll,
        "watch": cmd_watch,
        "status": cmd_status,
        "logs": cmd_logs,
        "config": cmd_config,
    }

    print(BANNER)
    commands[args.command](args, config)


if __name__ == "__main__":
    main()
