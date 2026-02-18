```
  ███████╗██╗███╗   ██╗ ██████╗ ███████╗██████╗     ██╗      ██████╗  ██████╗██╗  ██╗
  ██╔════╝██║████╗  ██║██╔════╝ ██╔════╝██╔══██╗    ██║     ██╔═══██╗██╔════╝██║ ██╔╝
  █████╗  ██║██╔██╗ ██║██║  ███╗█████╗  ██████╔╝    ██║     ██║   ██║██║     █████╔╝ 
  ██╔══╝  ██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗    ██║     ██║   ██║██║     ██╔═██╗ 
  ██║     ██║██║ ╚████║╚██████╔╝███████╗██║  ██║    ███████╗╚██████╔╝╚██████╗██║  ██╗
  ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
```

# 🔐 FingerLock

**Système de verrouillage intelligent par schéma tactile + détection d'activité**

Sécurisez votre ordinateur avec un **lock screen plein écran** stylé et un déverrouillage par **schéma 3×3** (style Android). FingerLock surveille votre activité clavier/souris et verrouille automatiquement après inactivité.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-fingerlock-blue)](https://pypi.org/project/fingerlock/)

---

## ✨ Fonctionnalités

### 🎨 Lock Screen Premium
- 🌈 **Écran plein** avec dégradé animé
- ⏰ **Horloge en temps réel**
- 🎯 **Grille 3×3** numérotée (1-9, style Android)
- ✨ **Animations fluides** (points pulse, lignes progressives)
- 🔊 **Sons subtils** (bips sur points, erreur, succès)
- 🖱️ **Tracé sans clic** — glissez simplement la souris
- ✅ **Zone de validation** intuitive

### 🔒 Sécurité Automatique
- ⌨️ **Détection clavier** via `evdev` (compatible Wayland)
- 🖱️ **Détection souris** native Linux
- ⏱️ **Délai configurable** (10s, 30s, 60s...)
- 🔐 **Schéma personnel** stocké hashé (SHA-256)
- 🚀 **Ultra-léger** — ~10MB RAM, 0% CPU idle

### 📊 Suivi & Logs
- 📝 Logs détaillés dans `~/.fingerlock/fingerlock.log`
- 🎯 Compteur d'events en temps réel
- 📈 Historique des verrouillages

---

## 🚀 Installation (2 commandes)

### Linux (Ubuntu/Debian)
```bash
# 1. Installer pipx
sudo apt install pipx && pipx ensurepath && source ~/.bashrc

# 2. Installer FingerLock
pipx install fingerlock

# 3. Lancer
fingerlock
```

### Autres distributions Linux
```bash
# Fedora/RHEL
sudo dnf install pipx && pipx ensurepath

# Arch
sudo pacman -S python-pipx && pipx ensurepath

# Puis
pipx install fingerlock && fingerlock
```

### Installation depuis le code source
```bash
git clone https://github.com/REBCDR07/fingerlock.git
cd fingerlock
pipx install .
fingerlock
```

---

## 📖 Premier lancement

Au démarrage, **deux écrans plein** s'affichent :

### Étape 1 : Dessinez votre schéma
```
┌─────────────────────────────────┐
│     🎨  Configuration          │
│                                 │
│   ┌───┬───┬───┐                │
│   │ 1 │ 2 │ 3 │                │
│   ├───┼───┼───┤                │
│   │ 4 │ 5 │ 6 │  ← Glissez     │
│   ├───┼───┼───┤     la souris  │
│   │ 7 │ 8 │ 9 │                │
│   └───┴───┴───┘                │
│                                 │
│       ✅  Valider               │
└─────────────────────────────────┘
```

**Exemple :** Tracez `7 → 5 → 3` = schéma diagonal

### Étape 2 : Confirmez le schéma

Redessinez le même schéma pour valider.

### Étape 3 : Délai d'inactivité
```
⏱️  Délai avant verrouillage (secondes) [10] : 30
```

**C'est tout ! La surveillance démarre. 🎉**

---

## 🎮 Utilisation

### Commandes disponibles
```bash
# Démarrer la surveillance (défaut)
fingerlock
fingerlock start

# Avec délai personnalisé
fingerlock start -d 60        # 60 secondes

# Voir la config actuelle
fingerlock config

# Éditer la configuration
fingerlock config --edit

# Réinitialiser le schéma
fingerlock reset

# État du système
fingerlock status

# Consulter les logs
fingerlock logs
fingerlock logs -n 100        # 100 dernières lignes
```

### Arrêter la surveillance

`Ctrl+C` dans le terminal

---

## 🔓 Déverrouillage

Après inactivité, l'écran de lock apparaît :
```
┌──────────────────────────────────────────┐
│                                          │
│           ⏰  14:35:22                   │
│        Mardi 18 Février 2026            │
│                                          │
│      🔒  Système verrouillé             │
│                                          │
│         7 → 5 → 3  ← Schéma actuel      │
│                                          │
│    ┌───┬───┬───┐                        │
│    │ 1 │ 2 │ 3 │   Glissez votre       │
│    ├───┼───┼───┤   schéma sur les      │
│    │ 4 │ 5 │ 6 │   points, puis        │
│    ├───┼───┼───┤   passez sur ✅       │
│    │ 7 │ 8 │ 9 │                        │
│    └───┴───┴───┘                        │
│                                          │
│         ✅  Valider                      │
│                                          │
│      Tentative 1/3                      │
└──────────────────────────────────────────┘
```

**3 tentatives max** puis arrêt du programme.

---

## ⚙️ Configuration

Fichier : `~/.fingerlock/config.yaml`
```yaml
# Délai d'inactivité (secondes)
lock_delay_seconds: 30

# Schéma (hashé SHA-256)
pattern_hash: d6a69166d21ee0c8a97327cb142adee2201749599f194a27453fc23edc0cde07
pattern_code: '12369'  # Pour debug uniquement

# Logs
log_path: /home/user/.fingerlock/fingerlock.log

# Plateforme (auto)
platform_lock: auto
```

**Modifier :**
```bash
fingerlock config --edit
nano ~/.fingerlock/config.yaml
```

---

## 🖥️ Compatibilité

### ✅ Linux

| Distribution | Version | Statut |
|--------------|---------|--------|
| Ubuntu | 20.04+ | ✅ Testé |
| Debian | 11+ | ✅ Compatible |
| Fedora | 35+ | ✅ Compatible |
| Arch Linux | Rolling | ✅ Compatible |
| Pop!_OS | 22.04+ | ✅ Testé |

**Sessions supportées :**
- 🌊 **Wayland** (via `evdev`) ✅
- 🪟 **X11** (via `evdev`) ✅

**Environnements de bureau :**
- GNOME, KDE Plasma, XFCE, i3wm, Sway

**Prérequis Linux :**
```bash
# Ajouter utilisateur au groupe input (si pas déjà fait)
sudo usermod -aG input $USER
# Redémarrer la session
```

### ⚠️ macOS

**Statut :** En cours de développement
- Détection d'activité : ⚠️ Limitations macOS
- Lock screen : ✅ Compatible

### ⚠️ Windows

**Statut :** En cours de développement
- Détection d'activité : ⚠️ Nécessite adaptations
- Lock screen : ✅ Compatible

---

## 📊 Exemple de logs
```log
2026-02-18T09:37:14 | INFO  | [09:37:14] ℹ️  SYSTEM  Surveillance démarrée
2026-02-18T09:37:14 | INFO  | [09:37:14] 📡 SYSTEM  11 périphériques détectés
2026-02-18T09:38:38 | WARN  | [09:38:38] 🔒 LOCK    Verrouillage après 30s
2026-02-18T09:38:48 | INFO  | [09:38:48] ℹ️  SYSTEM  Système déverrouillé
```

---

## 🛠️ Développement

### Cloner le projet
```bash
git clone https://github.com/REBCDR07/fingerlock.git
cd fingerlock
```

### Installer en mode dev
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
fingerlock
```

### Structure du projet
```
fingerlock/
├── fingerlock/
│   ├── __init__.py
│   ├── cli.py                 # Interface CLI
│   ├── core/
│   │   ├── watch.py           # Surveillance evdev
│   │   ├── lockscreen.py      # UI plein écran
│   │   ├── pattern_gui.py     # Setup schéma
│   │   └── locker.py          # Verrouillage système
│   ├── utils/
│   │   └── logger.py          # Journalisation
│   └── config/
│       └── settings.py        # Config YAML
├── setup.py
├── README.md
└── LICENSE
```

### Contribuer

1. Fork le projet
2. Créez une branche (`git checkout -b feature/ma-feature`)
3. Committez (`git commit -m 'Ajout feature X'`)
4. Push (`git push origin feature/ma-feature`)
5. Ouvrez une Pull Request

---

## 🆘 Dépannage

### ❌ "Commande 'fingerlock' introuvable"
```bash
pipx ensurepath
source ~/.bashrc
pipx reinstall fingerlock
```

### ❌ "Aucun périphérique input accessible"
```bash
# Vérifier le groupe input
groups $USER | grep input

# Si absent :
sudo usermod -aG input $USER
# Redémarrer la session (logout/login)
```

### ❌ "Events détectés: 0" (ne détecte pas l'activité)
```bash
# Vérifier les permissions /dev/input
ls -la /dev/input/event*

# Doivent être lisibles par le groupe 'input'
# Si problème, redémarrer après avoir ajouté au groupe
```

### ❌ Lock screen ne s'affiche pas
```bash
# Vérifier tkinter
python3 -c "import tkinter; print('OK')"

# Si erreur, installer :
sudo apt install python3-tk
```

### ❌ Sons ne fonctionnent pas

Normal ! Les sons utilisent `paplay` (PulseAudio). Si absent, FingerLock fonctionne sans sons.

---

## 📜 Licence

**MIT License** — Voir [LICENSE](LICENSE)

Copyright © 2026 Elton Ronald Bill HOUNNOU

---

## 👤 Auteur

### **Elton Ronald Bill HOUNNOU**

🚀 **Développeur Frontend** | Passionné par la Tech & l'IA

- 🌐 **LinkedIn** : [in/elton27](https://linkedin.com/in/elton27)
- 💻 **GitHub** : [REBCDR07](https://github.com/REBCDR07)
- 🦊 **GitLab** : [eltonhounnou2](https://gitlab.com/eltonhounnou2)
- 📧 **Email** : [eltonhounnou27@gmail.com](mailto:eltonhounnou27@gmail.com)
- 📱 **Téléphone** : +229 01 40 66 33 49

---

## 🙏 Remerciements

- [evdev](https://github.com/gvalkov/python-evdev) — Détection d'activité Linux native
- [tkinter](https://docs.python.org/3/library/tkinter.html) — Interface graphique
- Communauté Python 🐍

---

## 📈 Roadmap

- [ ] Support macOS natif (via Quartz)
- [ ] Support Windows (via pywin32)
- [ ] Mode daemon (lancement au boot)
- [ ] Interface de configuration graphique
- [ ] Multi-utilisateurs
- [ ] Thèmes personnalisables
- [ ] Export/Import de configuration

---

## 📝 Changelog

### v2.0.0 & v2.1.0 (2026-02-18) — Lock Screen Premium

- ✨ **Lock screen plein écran** animé avec dégradé
- 🎯 **Schéma 3×3** (1-9) avec tracé souris sans clic
- 🔊 **Sons** (bips sur points, erreur, succès)
- ⏰ **Horloge temps réel** + date
- ⚡ **Détection evdev** (compatible Wayland)
- 📊 **Debug mode** avec compteur d'events
- 🎨 **Animations** (pulse points, lignes progressives)

### v1.0.0 (2026-02-16) — Release Initiale

- 🎉 Première version publique
- ⌨️ Détection clavier/souris (pynput)
- 🔒 Verrouillage automatique
- 📦 Package PyPI

---

**⭐ Si FingerLock vous est utile, donnez une étoile sur [GitHub](https://github.com/REBCDR07/fingerlock) !**

---

<div align="center">
  
**Made with ❤️ by Elton Ronald Bill HOUNNOU**

[🐛 Reporter un bug](https://github.com/REBCDR07/fingerlock/issues) • [✨ Demander une feature](https://github.com/REBCDR07/fingerlock/issues) • [💬 Discussions](https://github.com/REBCDR07/fingerlock/discussions)

</div>
