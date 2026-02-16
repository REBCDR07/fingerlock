"""
config/settings.py
------------------
Gestion de la configuration de FaceLock.

Fichier de config par défaut : config.yaml (même répertoire que main.py).
Les valeurs CLI ont toujours la priorité sur le fichier.

Clés supportées :
    camera_id               int     Index de la webcam (0 par défaut)
    recognition_threshold   float   Distance max pour un match (plus petit = plus strict)
    lock_delay_seconds      int     Délai avant verrouillage après absence détectée
    embedding_path          str     Chemin vers le fichier .npy des embeddings
    log_path                str     Chemin vers le fichier de logs
    platform_lock           str     Commande de lock : "auto" | "windows" | "macos" | "linux"
    mediapipe_confidence    float   Confiance min pour la détection MediaPipe (0–1)
    capture_count           int     Nombre de frames captées lors de l'enrôlement
"""

import os
import yaml
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Répertoire racine du projet (là où se trouve main.py)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Valeurs par défaut
# ---------------------------------------------------------------------------
DEFAULTS: Dict[str, Any] = {
    "camera_id": 0,
    "recognition_threshold": 0.6,        # distance euclidienne max (face_recognition)
    "lock_delay_seconds": 5,             # secondes d'absence avant lock
    "embedding_path": os.path.join(PROJECT_ROOT, "data", "owner_embedding.npy"),
    "log_path": os.path.join(PROJECT_ROOT, "logs", "facelock.log"),
    "platform_lock": "auto",             # auto-détection du système
    "mediapipe_confidence": 0.5,         # seuil de détection MediaPipe
    "capture_count": 30,                 # frames pour l'enrôlement
}

CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.yaml")


# ---------------------------------------------------------------------------
# Chargement & validation
# ---------------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """
    Charge la config depuis config.yaml.
    Les clés manquantes sont complétées par DEFAULTS.
    Les chemins relatifs (embedding_path, log_path) sont résolus
    par rapport à PROJECT_ROOT pour garantir la stabilité quelle que soit la CWD.
    """
    config = dict(DEFAULTS)

    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        config.update(user_cfg)

    # ── Résolution des chemins relatifs → absolus par rapport à PROJECT_ROOT ──
    for path_key in ("embedding_path", "log_path"):
        if path_key in config and not os.path.isabs(config[path_key]):
            config[path_key] = os.path.join(PROJECT_ROOT, config[path_key])

    _validate(config)
    _ensure_directories(config)
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Sauvegarde la config actuelle dans config.yaml."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def print_config(config: Dict[str, Any]) -> None:
    """Affiche la config de manière lisible dans le terminal."""
    width = max(len(k) for k in config)
    for key, val in config.items():
        print(f"    {key:<{width}}  →  {val}")


# ---------------------------------------------------------------------------
# Validation interne
# ---------------------------------------------------------------------------
def _validate(cfg: Dict[str, Any]) -> None:
    """Vérifie la cohérence des valeurs de config."""
    if not (0.0 <= cfg["recognition_threshold"] <= 1.0):
        raise ValueError("recognition_threshold doit être entre 0.0 et 1.0")
    if cfg["lock_delay_seconds"] < 1:
        raise ValueError("lock_delay_seconds doit être >= 1")
    if not (0.0 <= cfg["mediapipe_confidence"] <= 1.0):
        raise ValueError("mediapipe_confidence doit être entre 0.0 et 1.0")
    if cfg["platform_lock"] not in ("auto", "windows", "macos", "linux"):
        raise ValueError("platform_lock : 'auto' | 'windows' | 'macos' | 'linux'")


def _ensure_directories(cfg: Dict[str, Any]) -> None:
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    for path_key in ("embedding_path", "log_path"):
        directory = os.path.dirname(cfg[path_key])
        if directory:
            os.makedirs(directory, exist_ok=True)
