# 🔒 FingerLock – Sécurité par Reconnaissance de Doigts

Application de sécurité par vision ordinateur, fonionnant en ligne de commande.
Elle surveille en temps réel la webcam et verrouille automatiquement le système
si le propriétaire n'est plus détecté ou si un visage non autorisé apparaît.

---

## 📐 Architecture du projet

```
facelock/
├── main.py                     ← Point d'entrée CLI (argparse)
├── config.yaml                 ← Configuration utilisateur (YAML)
├── requirements.txt            ← Dépendances pip
│
├── config/
│   ├── __init__.py
│   └── settings.py             ← Chargement / validation config
│
├── core/                       ← Logique métier
│   ├── __init__.py
│   ├── enroll.py               ← Enrôlement du propriétaire
│   ├── watch.py                ← Boucle de surveillance
│   └── locker.py               ← Verrouillage cross-plateforme
│
├── utils/                      ← Utilitaires transversaux
│   ├── __init__.py
│   └── logger.py               ← Journalisation structurée
│
├── scripts/
│   └── install_deps.py         ← Script d'installation des dépendances
│
├── data/
│   └── owner_embedding.npy     ← Embedding propriétaire (généré, non commité)
│
├── logs/
│   └── facelock.log            ← Journal d'événements
│
└── .gitignore
```

### Flux de données

```
Webcam (OpenCV)
       │
       ▼
MediaPipe FaceMesh          ← Détection rapide (CPU)
       │  visage détecté ?
       ▼
face_recognition            ← Extraction embedding 128-d (dlib)
       │
       ▼
Comparaison avec            ← Distance euclidienne
owner_embedding.npy            < threshold → propriétaire
       │                       > threshold → intrus
       ▼
Machine à états             ← UNLOCKED / ABSENCE_PENDING / LOCKED
       │
       ▼
locker.py                   ← lock_system() cross-plateforme
```

---

## ⚡ Installation rapide

### 1. Prérequis

- **Python >= 3.8** (recommandé : 3.9 – 3.11)
- Une **webcam** fonctionnelle et autorisée par le système
- Pour **Linux** : un gestionnaire de session avec support verrouillage
  (`gnome-screensaver`, `xscreensaver`, `i3lock`, ou `swaylock`)

### 2. Cloner le projet

```bash
git clone https://github.com/votre-compte/facelock.git
cd facelock
```

### 3. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# ou : venv\Scripts\activate    # Windows
```

### 4. Installer les dépendances

**Option A – pip directement :**
```bash
pip install -r requirements.txt
```

**Option B – script interactif (avec conseils plateforme) :**
```bash
python scripts/install_deps.py
```

**Option C – vérification uniquement :**
```bash
python scripts/install_deps.py --check
```

---

## 🚀 Utilisation

### Étape 1 : Enrôlement du propriétaire

Enregistre votre visage dans le système. À faire **une seule fois**.

```bash
python main.py enroll
```

Le script :
1. Ouvre la webcam
2. Détecte votre visage via MediaPipe
3. Capture 30 frames et extrait les embeddings
4. Sauvegarde un vecteur moyenné dans `data/owner_embedding.npy`

**Options :**
```bash
python main.py enroll -c 1      # Utiliser la caméra index 1
```

### Étape 2 : Surveillance en temps réel

```bash
python main.py watch
```

Le système :
- Détecte et reconnaît votre visage en continu
- Reste **déverrouillé** tant que vous êtes devant la caméra
- Déclenche un **décompte** si votre visage disparaît
- **Verrouille** le PC après le délai configuré

**Options CLI (ont la priorité sur config.yaml) :**
```bash
python main.py watch -t 0.55          # Seuil de reconnaissance plus strict
python main.py watch -d 10            # 10 secondes avant verrouillage
python main.py watch -c 1             # Caméra index 1
python main.py watch -t 0.55 -d 3    # Combiner plusieurs options
```

### Autres commandes

```bash
# Afficher l'état actuel du système
python main.py status

# Afficher les derniers logs (30 lignes par défaut)
python main.py logs
python main.py logs -n 50             # 50 dernières lignes

# Afficher la configuration en cours
python main.py config
```

---

## ⚙️ Configuration

Tous les paramètres sont dans **`config.yaml`** à la racine du projet.

| Clé | Type | Défaut | Description |
|-----|------|--------|-------------|
| `camera_id` | int | `0` | Index de la webcam (0 = première) |
| `recognition_threshold` | float | `0.60` | Distance max pour un match (plus petit = plus strict) |
| `lock_delay_seconds` | int | `5` | Secondes d'absence avant verrouillage |
| `embedding_path` | str | `data/owner_embedding.npy` | Chemin du fichier d'embedding |
| `log_path` | str | `logs/facelock.log` | Chemin du fichier de logs |
| `platform_lock` | str | `auto` | Plateforme : `auto` / `windows` / `macos` / `linux` |
| `mediapipe_confidence` | float | `0.5` | Confiance min MediaPipe (0–1) |
| `capture_count` | int | `30` | Frames captées lors de l'enrôlement |

### Guide du seuil de reconnaissance

| Valeur | Comportement |
|--------|--------------|
| `0.45` | Très strict – peu de faux positifs, risque de vous bloquer vous-même |
| `0.50` | Strict – bon équilibre sécurité |
| `0.60` | **Par défaut** – équilibre général recommandé |
| `0.70` | Permissif – risque de reconnaissance de visages similaires |

---

## 📋 Journalisation

Tous les événements sont loggués dans `logs/facelock.log` :

```
2025-06-15T10:30:42 | INFO     | [10:30:42] 📸 ENROLL     Démarrage de l'enrôlement du propriétaire.
2025-06-15T10:30:55 | INFO     | [10:30:55] 📸 ENROLL     Enrôlement réussi. Embedding sauvegardé → data/owner_embedding.npy
2025-06-15T10:31:10 | INFO     | [10:31:10] ℹ️  SYSTEM     Surveillance démarrée – threshold=0.6, delay=5s
2025-06-15T10:31:12 | INFO     | [10:31:12] ✅ PRESENCE   Propriétaire présent (dist=0.42)
2025-06-15T10:31:45 | WARNING  | [10:31:45] ⚠️  ABSENCE   Aucun visage détecté – décompte verrouillage.
2025-06-15T10:31:50 | WARNING  | [10:31:50] 🔒 LOCK       Délai écoulé – verrouillage du système.
2025-06-15T10:31:50 | WARNING  | [10:31:50] 🔒 LOCK       Système verrouillé avec succès.
```

Catégories des événements :
- **PRESENCE** – visage du propriétaire reconnu
- **ABSENCE** – disparition détectée, décompte en cours
- **LOCK** – verrouillage déclenché ou réussi
- **SYSTEM** – démarrage, arrêt, config chargée
- **ENROLL** – événements d'enrôlement
- **ERROR** – erreurs techniques

---

## 🛠️ Résolution des problèmes

### ❌ "Caméra non disponible"
- Vérifiez l'index avec `python main.py config` puis essayez `-c 0`, `-c 1`, `-c 2`
- Sur macOS : autorisez l'accès caméra à Python dans les Préférences Système
- Sur Linux : vérifiez que votre utilisateur est dans le groupe `video` : `sudo usermod -aG video $USER`

### ❌ "Aucun visage détecté" pendant l'enrôlement
- Restez directement face à la caméra, à 30–60 cm
- Vérifiez l'éclairage (évitez le contre-jour)
- Baissez `mediapipe_confidence` dans `config.yaml` (ex : `0.3`)

### ❌ Reconnaissance peu fiable en surveillance
- **Trop de faux positifs** (vous n'êtes pas reconnu) → montez le threshold (`0.65` – `0.70`)
- **Trop de faux négatifs** (intrus reconnu comme vous) → baissez le threshold (`0.50` – `0.45`)
- Ré-enrôlez-vous dans des conditions d'éclairage proches de votre environnement habituel

### ❌ Verrouillage ne fonctionne pas (Linux)
Installez un backend compatible :
```bash
sudo apt install gnome-screensaver      # Bureau GNOME
sudo apt install xscreensaver           # X11 générique
# ou : i3lock, swaylock selon votre window manager
```

### ❌ Erreur d'installation `face_recognition`
Cette bibliothèque compile `dlib` depuis les sources. Il faut :
- **Windows** : Visual Studio Build Tools + cmake (`pip install cmake`)
- **macOS** : Xcode Command Line Tools (`xcode-select --install`)
- **Linux** : `sudo apt install python3-dev build-essential cmake`

---

## 🧩 Extension & contribution

Le projet est architecturé pour être extensible :

- **Nouveau backend de verrouillage** → ajoutez une entrée dans `_LOCK_COMMANDS` dans `core/locker.py`
- **Nouveau mode de détection** → créez un nouveau module dans `core/` et appelez-le depuis `watch.py`
- **Notifications (SMS, email, push)** → étendez la fonction `_handle_absence()` dans `watch.py`
- **Interface graphique** → créez un module `ui/` qui consomme les mêmes modules `core/`

---

## 📜 Licence & sécurité

- Les données biométriques (`owner_embedding.npy`) sont stockées **localement uniquement**
- Le fichier est exclu du contrôle de version via `.gitignore`
- Aucune donnée n'est envoyée sur le réseau
- Pour une utilisation en production, considérez le chiffrement du fichier d'embedding au repos
