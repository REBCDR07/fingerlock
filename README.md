```
 _____ _                       _                _    
|  ___(_)_ __   __ _  ___ _ __| |    ___   ___| | __
| |_  | | '_ \ / _` |/ _ \ '__| |   / _ \ / __| |/ /
|  _| | | | | | (_| |  __/ |  | |__| (_) | (__|   < 
|_|   |_|_| |_|\__, |\___|_|  |_____\___/ \___|_|\_\
               |___/                                 
```

# FingerLock 🔒

**Sécurité automatique par détection d'activité clavier/souris**

FingerLock verrouille automatiquement votre ordinateur après une période d'inactivité, détectée via votre clavier et votre souris. Plus besoin de verrouiller manuellement votre PC quand vous partez !

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | macOS | Windows](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)]()

---

## ✨ Fonctionnalités

- ⌨️ **Détection clavier** — Chaque touche réinitialise le timer
- 🖱️ **Détection souris** — Mouvements et clics gardent le système actif
- 🔒 **Verrouillage automatique** — Lock après X secondes d'inactivité
- ⚡ **Ultra-léger** — Consommation CPU/RAM minimale
- 🎯 **Multi-plateforme** — Linux, macOS, Windows
- 📊 **Logs détaillés** — Historique complet des événements
- ⚙️ **Configuration simple** — Setup interactif au premier lancement

---

## 🚀 Installation Rapide

### Prérequis

- Python 3.8 ou supérieur
- pip ou pipx

### Installation avec pipx (recommandé)
```bash
# 1. Installer pipx (si pas déjà fait)
# Ubuntu/Debian
sudo apt install pipx
pipx ensurepath

# macOS
brew install pipx
pipx ensurepath

# Windows
pip install pipx
pipx ensurepath

# 2. Installer FingerLock
pipx install git+https://github.com/REBCDR07/fingerlock.git

# 3. Lancer
fingerlock
```

### Installation avec pip
```bash
pip install git+https://github.com/REBCDR07/fingerlock.git
fingerlock
```

### Installation depuis les sources
```bash
git clone https://github.com/REBCDR07/fingerlock.git
cd fingerlock
pipx install .
fingerlock
```

---

## 📖 Utilisation

### Premier lancement

Au premier démarrage, FingerLock vous demande la configuration :
```bash
$ fingerlock

 _____ _                       _                _    
|  ___(_)_ __   __ _  ___ _ __| |    ___   ___| | __
| |_  | | '_ \ / _` |/ _ \ '__| |   / _ \ / __| |/ /
|  _| | | | | | (_| |  __/ |  | |__| (_) | (__|   < 
|_|   |_|_| |_|\__, |\___|_|  |_____\___/ \___|_|\_\
               |___/                                 
        Sécurité par Reconnaissance de Doigts
        ======================================

  🎉 Bienvenue dans FingerLock !

  Configuration initiale :

  ⏱️  Délai d'inactivité avant verrouillage (en secondes) [10] : 15

  ✅ Configuration sauvegardée dans : /home/user/.fingerlock/config.yaml
  📝 Délai configuré : 15 secondes
```

La surveillance démarre automatiquement !

### Commandes disponibles
```bash
# Démarrer la surveillance (commande par défaut)
fingerlock
fingerlock start

# Avec un délai personnalisé (override la config)
fingerlock start -d 30

# Voir la configuration actuelle
fingerlock config

# Éditer la configuration
fingerlock config --edit

# Afficher l'état du système
fingerlock status

# Voir les logs
fingerlock logs
fingerlock logs -n 50  # 50 dernières lignes
```

### Arrêter la surveillance

Appuyez sur **Ctrl+C** dans le terminal où tourne FingerLock.

---

## ⚙️ Configuration

Le fichier de configuration est situé dans `~/.fingerlock/config.yaml` :
```yaml
# Délai d'inactivité en secondes
lock_delay_seconds: 10

# Plateforme de verrouillage (auto-détection)
platform_lock: auto

# Fichier de logs
log_path: /home/user/.fingerlock/fingerlock.log
```

**Modifier la configuration :**
```bash
fingerlock config --edit
```

Ou directement :
```bash
nano ~/.fingerlock/config.yaml
```

---

## 🖥️ Compatibilité Plateformes

### Linux

**Gestionnaires de sessions supportés :**
- GNOME (gnome-screensaver)
- KDE Plasma
- XFCE
- i3wm (i3lock)
- Sway (swaylock)
- Xscreensaver

**Installation du backend de verrouillage :**
```bash
# GNOME (Ubuntu standard)
sudo apt install gnome-screensaver

# X11 générique
sudo apt install xscreensaver

# i3wm
sudo apt install i3lock

# Sway (Wayland)
sudo apt install swaylock
```

### macOS

Utilise la commande système native. Aucune configuration requise.

**Permissions nécessaires :**
- Accessibilité (pour détecter clavier/souris)

### Windows

Utilise `rundll32` natif. Aucune configuration requise.

---

## 📊 Logs

Les événements sont enregistrés dans `~/.fingerlock/fingerlock.log` :
```
2025-02-16T16:27:00 | INFO     | [16:27:00] ℹ️  SYSTEM     Surveillance inputs démarrée
2025-02-16T16:27:15 | WARNING  | [16:27:15] 🔒 LOCK       Verrouillage après 10s d'inactivité
2025-02-16T16:27:20 | INFO     | [16:27:20] ℹ️  SYSTEM     Système déverrouillé
```

**Catégories d'événements :**
- `SYSTEM` — Démarrage, arrêt, configuration
- `LOCK` — Verrouillages automatiques
- `ERROR` — Erreurs techniques

---

## 🔧 Développement

### Cloner et installer en mode dev
```bash
git clone https://github.com/REBCDR07/fingerlock.git
cd fingerlock
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -e .
fingerlock
```

### Structure du projet
```
fingerlock/
├── fingerlock/
│   ├── __init__.py
│   ├── cli.py           # Point d'entrée CLI
│   ├── core/
│   │   ├── watch.py     # Boucle de surveillance
│   │   └── locker.py    # Verrouillage cross-plateforme
│   ├── utils/
│   │   └── logger.py    # Journalisation
│   └── config/
├── setup.py
├── README.md
└── LICENSE
```

### Tests
```bash
# Tester la détection d'activité
fingerlock start -d 5

# Vérifier les logs
fingerlock logs -n 20
```

---

## 🆘 Dépannage

### ❌ "Commande 'fingerlock' introuvable"

**Solution :**
```bash
# Vérifier que pipx est dans le PATH
pipx ensurepath
source ~/.bashrc

# Réinstaller
pipx reinstall fingerlock
```

### ❌ "ModuleNotFoundError: No module named 'fingerlock'"

**Solution :**
```bash
pipx uninstall fingerlock
pipx install git+https://github.com/REBCDR07/fingerlock.git
```

### ❌ Verrouillage ne fonctionne pas (Linux)

**Solution :**
```bash
# Tester manuellement
gnome-screensaver-command -l

# Si erreur, installer :
sudo apt install gnome-screensaver
```

### ❌ Détection clavier/souris ne fonctionne pas

**Linux :** Vérifiez que votre utilisateur a les permissions :
```bash
# Ajouter au groupe input
sudo usermod -aG input $USER
# Redémarrer la session
```

**macOS :** Autorisez l'accès "Accessibilité" dans :
```
Préférences Système → Sécurité → Confidentialité → Accessibilité
```

---

## 🤝 Contribuer

Les contributions sont les bienvenues !

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

---

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👤 Auteur

**Elton Ronald Bill Hounnou**

- GitHub: [@VOTRE-USERNAME](https://github.com/REBCDR07)
- Email: eltonhounnou27@gmail.com

---

## 🙏 Remerciements

- [pynput](https://github.com/moses-palmer/pynput) — Détection clavier/souris
- [opencv-python](https://github.com/opencv/opencv-python) — Traitement vidéo (versions antérieures)

---

## 📝 Changelog

### Version 1.0.0 (2026-02-16)

- 🎉 Release initiale
- ⌨️ Détection clavier et souris
- 🔒 Verrouillage automatique multi-plateforme
- 📊 Système de logs
- ⚙️ Configuration interactive
- 📦 Package pip installable

---

**⭐ Si ce projet vous est utile, n'hésitez pas à lui donner une étoile sur GitHub !**
