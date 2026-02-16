#!/usr/bin/env python3
"""
FingerLock – Point d'entrée CLI
"""
import argparse
import sys
import os
from pathlib import Path

# Banner
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

def get_config_dir():
    """Répertoire de config dans le home de l'utilisateur"""
    home = Path.home()
    config_dir = home / ".fingerlock"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def first_time_setup():
    """Configuration initiale au premier lancement"""
    config_dir = get_config_dir()
    config_file = config_dir / "config.yaml"
    
    if config_file.exists():
        return  # Déjà configuré
    
    print(BANNER)
    print("  🎉 Bienvenue dans FingerLock !\n")
    print("  Configuration initiale :\n")
    
    # Demander le délai
    while True:
        try:
            delay = input("  ⏱️  Délai d'inactivité avant verrouillage (en secondes) [10] : ").strip()
            if not delay:
                delay = 10
            else:
                delay = int(delay)
            
            if delay < 1:
                print("  ❌ Le délai doit être au moins 1 seconde\n")
                continue
            break
        except ValueError:
            print("  ❌ Veuillez entrer un nombre entier\n")
    
    # Créer le fichier de config
    import yaml
    config = {
        "lock_delay_seconds": delay,
        "platform_lock": "auto",
        "log_path": str(config_dir / "fingerlock.log"),
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    print(f"\n  ✅ Configuration sauvegardée dans : {config_file}")
    print(f"  📝 Délai configuré : {delay} secondes\n")
    print("  Pour modifier la configuration plus tard :")
    print(f"      nano {config_file}\n")

def load_user_config():
    """Charge la config depuis ~/.fingerlock/config.yaml"""
    import yaml
    config_file = get_config_dir() / "config.yaml"
    
    if not config_file.exists():
        first_time_setup()
    
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def cmd_start(args):
    """Démarrer la surveillance"""
    from fingerlock.core.watch import run_watch
    from fingerlock.utils.logger import setup_logger
    
    config = load_user_config()
    
    # Override CLI si fourni
    if args.delay:
        config["lock_delay_seconds"] = args.delay
    
    # Setup logging
    log_path = config.get("log_path", str(get_config_dir() / "fingerlock.log"))
    setup_logger(log_path)
    
    print(BANNER)
    print(f"  🚀 Démarrage de la surveillance...")
    print(f"  ⏱️  Délai d'inactivité : {config['lock_delay_seconds']}s\n")
    
    run_watch(config)

def cmd_config(args):
    """Afficher ou modifier la configuration"""
    config_file = get_config_dir() / "config.yaml"
    
    if args.edit:
        import subprocess
        editor = os.environ.get('EDITOR', 'nano')
        subprocess.run([editor, str(config_file)])
    else:
        print(BANNER)
        print("  📋 Configuration actuelle :\n")
        config = load_user_config()
        for key, val in config.items():
            print(f"      {key:<25} → {val}")
        print(f"\n  📁 Fichier : {config_file}")
        print(f"  ✏️  Modifier : fingerlock config --edit\n")

def cmd_status(args):
    """Afficher l'état du système"""
    print(BANNER)
    config = load_user_config()
    
    print("  ── État du système ──\n")
    print(f"  Délai d'inactivité  : {config.get('lock_delay_seconds', 10)}s")
    print(f"  Plateforme de lock  : {config.get('platform_lock', 'auto')}")
    print(f"  Fichier de logs     : {config.get('log_path', 'N/A')}")
    print()

def cmd_logs(args):
    """Afficher les logs"""
    config = load_user_config()
    log_file = Path(config.get("log_path", ""))
    
    if not log_file.exists():
        print("\n  ⚠️  Aucun fichier de logs trouvé")
        print("      Lancez d'abord : fingerlock start\n")
        return
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    n = args.lines or 30
    recent = lines[-n:] if len(lines) > n else lines
    
    print(f"\n  ── Dernières {n} entrées de log ──\n")
    for line in recent:
        print(f"    {line.rstrip()}")
    print()

def build_parser():
    parser = argparse.ArgumentParser(
        prog="fingerlock",
        description="🔒 FingerLock – Sécurité automatique par détection d'activité",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # fingerlock start
    p_start = subparsers.add_parser("start", help="Démarrer la surveillance")
    p_start.add_argument("-d", "--delay", type=int, help="Délai en secondes (override config)")
    
    # fingerlock config
    p_config = subparsers.add_parser("config", help="Afficher/modifier la configuration")
    p_config.add_argument("--edit", action="store_true", help="Éditer le fichier de config")
    
    # fingerlock status
    subparsers.add_parser("status", help="Afficher l'état du système")
    
    # fingerlock logs
    p_logs = subparsers.add_parser("logs", help="Afficher les logs")
    p_logs.add_argument("-n", "--lines", type=int, help="Nombre de lignes")
    
    return parser

def main():
    """Point d'entrée principal"""
    parser = build_parser()
    args = parser.parse_args()
    
    # Si aucune commande, démarrer par défaut
    if not args.command:
        args.command = "start"
        args.delay = None
    
    commands = {
        "start": cmd_start,
        "config": cmd_config,
        "status": cmd_status,
        "logs": cmd_logs,
    }
    
    commands[args.command](args)

if __name__ == "__main__":
    main()
