#!/usr/bin/env python3
"""
scripts/install_deps.py
-----------------------
Script d'installation automatique des dépendances FaceLock.

Usages :
    python scripts/install_deps.py          # Installation standard
    python scripts/install_deps.py --check  # Vérification uniquement (pas d'install)
    python scripts/install_deps.py --venv   # Créer + activer un venv automatiquement

Ce script :
    1. Vérifie la version de Python (>= 3.8)
    2. Liste les paquets nécessaires avec version minimale
    3. Détecte la plateforme pour des conseils spécifiques
    4. Lance pip install
    5. Vérifie l'import de chaque module critique
"""

import subprocess
import sys
import platform
import os

# ---------------------------------------------------------------------------
# Paquets requis : (nom_pip, version_min, nom_import, description)
# ---------------------------------------------------------------------------
REQUIRED_PACKAGES = [
    ("opencv-python",      "4.5.0",  "cv2",             "Capture caméra & traitement image"),
    ("mediapipe",          "0.8.0",  "mediapipe",       "Détection de visage temps réel"),
    ("face_recognition",   "1.3.0",  "face_recognition","Extraction & comparaison embeddings"),
    ("numpy",              "1.20.0", "numpy",           "Opérations numériques (embeddings)"),
    ("pyyaml",             "5.4.0",  "yaml",            "Lecture du fichier config.yaml"),
]

MIN_PYTHON = (3, 8)


def check_python() -> bool:
    """Vérifie la version de Python."""
    v = sys.version_info
    ok = (v.major, v.minor) >= MIN_PYTHON
    status = "✅" if ok else "❌"
    print(f"  {status}  Python {v.major}.{v.minor}.{v.micro}  (requis >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})")
    return ok


def check_packages() -> dict:
    """
    Vérifie quels paquets sont déjà installés.
    Retourne : { "installed": [...], "missing": [...] }
    """
    installed, missing = [], []

    for pip_name, min_ver, import_name, desc in REQUIRED_PACKAGES:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "?")
            print(f"  ✅  {pip_name:<25} v{ver:<10} – {desc}")
            installed.append(pip_name)
        except ImportError:
            print(f"  ❌  {pip_name:<25} {'NON INSTALLÉ':<10} – {desc}")
            missing.append(pip_name)

    return {"installed": installed, "missing": missing}


def install_packages(missing: list) -> bool:
    """Lance pip install pour les paquets manquants."""
    if not missing:
        print("\n  ✅  Tous les paquets sont déjà installés !")
        return True

    print(f"\n  📦  Installation de {len(missing)} paquet(s)…\n")
    cmd = [sys.executable, "-m", "pip", "install"] + missing + ["--upgrade"]

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        print("\n  ❌  Erreur lors de l'installation pip.")
        return False


def print_platform_tips():
    """Affiche des conseils spécifiques à la plateforme."""
    system = platform.system()
    print("\n  ── Conseils plateforme ──\n")

    if system == "Windows":
        print("  Windows :")
        print("    • face_recognition nécessite Visual Studio Build Tools")
        print("      → https://visualstudio.microsoft.com/downloads/ (Outils de compilation C++)")
        print("    • Si erreur cmake, installez cmake via pip : pip install cmake")
        print("    • Webcam : assurez-vous que les permissions sont accordées à Python.\n")

    elif system == "Darwin":
        print("  macOS :")
        print("    • Autorisez l'accès caméra à Python dans :")
        print("      Préférences Système → Sécurité → Confidentialité → Caméra")
        print("    • Si erreur de compilation, installez Xcode Command Line Tools :")
        print("      xcode-select --install")
        print("    • Pour le verrouillage, autorisez aussi 'Accessibilité'.\n")

    elif system == "Linux":
        print("  Linux :")
        print("    • Installez les dépendances système pour OpenCV :")
        print("      sudo apt install -y python3-dev build-essential libjpeg-dev libpng-dev")
        print("    • Pour MediaPipe sur certaines architectures :")
        print("      sudo apt install -y cmake pkg-config")
        print("    • Verrouillage : installez l'une des options :")
        print("      sudo apt install gnome-screensaver   # GNOME")
        print("      sudo apt install xscreensaver        # X11 générique")
        print("      # ou utilisez i3lock / swaylock si vous êtes sur i3/sway")
        print()


def setup_venv():
    """Crée un venv à côté du projet."""
    venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv")
    if os.path.isdir(venv_path):
        print(f"  ℹ️   Venv existe déjà : {venv_path}")
    else:
        print(f"  📦  Création du venv : {venv_path}")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    # Activer le venv (en modifiant sys.executable pour pip)
    if platform.system() == "Windows":
        activate_script = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        activate_script = os.path.join(venv_path, "bin", "python")

    print(f"  ✅  Venv prêt. Utilisez :")
    if platform.system() == "Windows":
        print(f"        venv\\Scripts\\activate")
    else:
        print(f"        source venv/bin/activate")
    print()
    return activate_script


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Installer les dépendances FaceLock")
    parser.add_argument("--check", action="store_true", help="Vérifier uniquement, pas d'installation")
    parser.add_argument("--venv", action="store_true", help="Créer un venv avant d'installer")
    args = parser.parse_args()

    print("\n  ══════════════════════════════════════")
    print("    FaceLock – Installation des dépendances")
    print("  ══════════════════════════════════════\n")

    # Vérifie Python
    if not check_python():
        print("\n  ❌  Python >= 3.8 requis. Arrêt.\n")
        sys.exit(1)

    # Venv optionnel
    if args.venv:
        setup_venv()

    # Conseils plateforme
    print_platform_tips()

    # Vérification des paquets
    print("  ── Paquets nécessaires ──\n")
    status = check_packages()

    if args.check:
        if status["missing"]:
            print(f"\n  ⚠️   {len(status['missing'])} paquet(s) manquant(s). Lancez sans --check pour installer.\n")
        else:
            print("\n  ✅  Tout est en ordre !\n")
        sys.exit(0)

    # Installation
    success = install_packages(status["missing"])

    if success:
        print("\n  ── Vérification post-installation ──\n")
        check_packages()
        print("\n  🎉  Installation terminée ! Lancez :")
        print("        python main.py enroll   →   pour vous enrôler")
        print("        python main.py watch    →   pour démarrer la surveillance\n")
    else:
        print("\n  ❌  Certains paquets n'ont pas pu être installés.")
        print("      Consultez les erreurs ci-dessus.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
