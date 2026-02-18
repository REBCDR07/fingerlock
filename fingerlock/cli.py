#!/usr/bin/env python3
"""FingerLock – Point d'entrée CLI"""
import argparse, sys, os
from pathlib import Path
import yaml

BANNER = r"""
 _____ _                       _                _    
|  ___(_)_ __   __ _  ___ _ __| |    ___   ___| | __
| |_  | | '_ \ / _` |/ _ \ '__| |   / _ \ / __| |/ /
|  _| | | | | | (_| |  __/ |  | |__| (_) | (__|   < 
|_|   |_|_| |_|\__, |\___|_|  |_____\___/ \___|_|\_\
               |___/                                 
        Sécurité par Schéma & Détection d'Activité
        ============================================
"""

def get_config_dir():
    config_dir = Path.home() / ".fingerlock"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def load_user_config():
    config_file = get_config_dir() / "config.yaml"

    if not config_file.exists():
        # Premier lancement : setup complet
        print(BANNER)
        print("  🎉 Bienvenue dans FingerLock !\n")

        from fingerlock.core.pattern_gui import setup_pattern_gui as setup_pattern
        config = setup_pattern(get_config_dir())

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        print(f"  ✅ Configuration sauvegardée !")
        print(f"  📁 Fichier : {config_file}\n")
        return config

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f) or {}

    config.setdefault("lock_delay_seconds", 10)
    config.setdefault("platform_lock", "auto")
    config.setdefault("log_path", str(get_config_dir() / "fingerlock.log"))
    return config

def cmd_start(args):
    from fingerlock.core.watch import run_watch
    from fingerlock.utils.logger import setup_logger

    config = load_user_config()

    if hasattr(args, 'delay') and args.delay:
        config["lock_delay_seconds"] = args.delay

    setup_logger(config["log_path"])
    print(BANNER)
    run_watch(config)

def cmd_config(args):
    config_file = get_config_dir() / "config.yaml"
    if hasattr(args, 'edit') and args.edit:
        import subprocess
        editor = os.environ.get('EDITOR', 'nano')
        subprocess.run([editor, str(config_file)])
    else:
        print(BANNER)
        print("  📋 Configuration actuelle :\n")
        config = load_user_config()
        for key, val in config.items():
            if key != "pattern_hash":  # Ne pas afficher le hash
                print(f"      {key:<25} → {val}")
        print(f"\n  📁 Fichier : {config_file}")
        print(f"  ✏️  Modifier : fingerlock config --edit\n")

def cmd_reset(args):
    """Réinitialiser le schéma"""
    config_file = get_config_dir() / "config.yaml"
    if config_file.exists():
        config_file.unlink()
        print("\n  ✅ Configuration supprimée.")
        print("  Lancez 'fingerlock' pour reconfigurer.\n")
    else:
        print("\n  ⚠️  Aucune configuration trouvée.\n")

def cmd_status(args):
    print(BANNER)
    config = load_user_config()
    print("  ── État du système ──\n")
    print(f"  ⏱️  Délai d'inactivité  : {config.get('lock_delay_seconds', 10)}s")
    print(f"  🔐 Schéma configuré    : {'✅ Oui' if config.get('pattern_hash') else '❌ Non'}")
    print(f"  🖥️  Plateforme de lock  : {config.get('platform_lock', 'auto')}")
    print(f"  📊 Fichier de logs     : {config.get('log_path', 'N/A')}")
    print()

def cmd_logs(args):
    config = load_user_config()
    log_file = Path(config.get("log_path", ""))
    if not log_file.exists():
        print("\n  ⚠️  Aucun fichier de logs trouvé.\n")
        return
    with open(log_file, 'r') as f:
        lines = f.readlines()
    n = args.lines if hasattr(args, 'lines') and args.lines else 30
    recent = lines[-n:] if len(lines) > n else lines
    print(f"\n  ── Dernières {n} entrées ──\n")
    for line in recent:
        print(f"    {line.rstrip()}")
    print()

def build_parser():
    parser = argparse.ArgumentParser(
        prog="fingerlock",
        description="🔒 FingerLock – Sécurité par schéma et détection d'activité",
    )
    sub = parser.add_subparsers(dest="command")

    # start
    p_start = sub.add_parser("start", help="Démarrer la surveillance")
    p_start.add_argument("-d", "--delay", type=int, help="Délai en secondes")

    # config
    p_config = sub.add_parser("config", help="Voir/modifier la configuration")
    p_config.add_argument("--edit", action="store_true", help="Éditer le fichier")

    # reset
    sub.add_parser("reset", help="Réinitialiser le schéma et la configuration")

    # status
    sub.add_parser("status", help="État du système")

    # logs
    p_logs = sub.add_parser("logs", help="Afficher les logs")
    p_logs.add_argument("-n", "--lines", type=int, help="Nombre de lignes")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        class DefaultArgs:
            command = "start"
            delay = None
        args = DefaultArgs()

    commands = {
        "start":  cmd_start,
        "config": cmd_config,
        "reset":  cmd_reset,
        "status": cmd_status,
        "logs":   cmd_logs,
    }
    commands[args.command](args)

if __name__ == "__main__":
    main()
