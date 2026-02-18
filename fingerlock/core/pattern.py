"""
FingerLock – Schéma par glissement trackpad avec stabilisation
"""
import hashlib
import time
import threading
from pynput import mouse as ms

GRID_DISPLAY = """
  ┌───┬───┬───┐
  │ 7 │ 8 │ 9 │
  ├───┼───┼───┤
  │ 4 │ 5 │ 6 │
  ├───┼───┼───┤
  │ 1 │ 2 │ 3 │
  └───┴───┴───┘
"""

def _hash_pattern(pattern: list) -> str:
    raw = "-".join(pattern)
    return hashlib.sha256(raw.encode()).hexdigest()

def _get_screen_size():
    try:
        import subprocess, re
        result = subprocess.run(['xrandr'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if ' connected' in line:
                match = re.search(r'(\d+)x(\d+)\+0\+0', line)
                if match:
                    return int(match.group(1)), int(match.group(2))
    except:
        pass
    return 1920, 1080

def _get_zone(x, y, screen_w, screen_h) -> str:
    col = max(0, min(2, int(x / (screen_w / 3))))
    row = max(0, min(2, int(y / (screen_h / 3))))
    return [['7','8','9'],['4','5','6'],['1','2','3']][row][col]

def _draw_pattern(pattern):
    """Affiche la grille avec schéma"""
    pos = {
        '7':(0,0),'8':(0,1),'9':(0,2),
        '4':(1,0),'5':(1,1),'6':(1,2),
        '1':(2,0),'2':(2,1),'3':(2,2),
    }
    rows = [['·','·','·'],['·','·','·'],['·','·','·']]
    for i, z in enumerate(pattern):
        r,c = pos[z]
        rows[r][c] = str(i+1) if i < 9 else '★'

    print("\033[H\033[J", end="")
    print("\n  ┌───┬───┬───┐")
    for i, row in enumerate(rows):
        print(f"  │ {row[0]} │ {row[1]} │ {row[2]} │")
        if i < 2:
            print("  ├───┼───┼───┤")
    print("  └───┴───┴───┘")

    if pattern:
        print(f"\n  Schéma : {' → '.join(pattern)}")
        print(f"  Points : {len(pattern)}/9")
    else:
        print(f"\n  👆 Appuyez et glissez lentement...")
    print(f"\n  Relâchez pour valider (min 3 points)")
    print(f"  Clic droit = annuler")


def capture_pattern(prompt: str, min_points: int = 3) -> list:
    """
    Capture schéma avec stabilisation :
    - Une zone est comptée seulement si le doigt y reste 150ms
    - Pas de doublons consécutifs
    - Pas d'aller-retour (5→6→5 interdit)
    """
    screen_w, screen_h = _get_screen_size()
    pattern = []
    drawing = False
    done = False
    cancelled = False

    # Stabilisation
    current_zone = None
    zone_enter_time = 0
    STABILITY_DELAY = 0.15  # 150ms dans une zone pour la valider

    print(f"\n  {prompt}")
    _draw_pattern(pattern)

    def on_click(x, y, button, pressed):
        nonlocal drawing, done, cancelled, current_zone, zone_enter_time

        if button == ms.Button.left:
            if pressed:
                drawing = True
                pattern.clear()
                current_zone = _get_zone(x, y, screen_w, screen_h)
                zone_enter_time = time.time()
                pattern.append(current_zone)
                _draw_pattern(pattern)
            else:
                # Relâcher
                drawing = False
                if len(pattern) >= min_points:
                    done = True
                    return False
                else:
                    print(f"\n  ❌ Trop court ({len(pattern)} points). Recommencez.")
                    time.sleep(1)
                    pattern.clear()
                    current_zone = None
                    _draw_pattern(pattern)

        elif button == ms.Button.right and pressed:
            cancelled = True
            return False

    def on_move(x, y):
        nonlocal current_zone, zone_enter_time

        if not drawing:
            return

        zone = _get_zone(x, y, screen_w, screen_h)

        if zone != current_zone:
            # On entre dans une nouvelle zone
            current_zone = zone
            zone_enter_time = time.time()

        else:
            # On reste dans la même zone
            time_in_zone = time.time() - zone_enter_time

            if time_in_zone >= STABILITY_DELAY:
                # Zone stabilisée !
                # Pas de doublon avec le dernier point
                if not pattern or pattern[-1] != zone:
                    # Pas d'aller-retour (pas de retour à l'avant-dernier)
                    if len(pattern) < 2 or pattern[-2] != zone:
                        pattern.append(zone)
                        _draw_pattern(pattern)
                        zone_enter_time = time.time() + 99999  # Bloquer re-capture

    with ms.Listener(on_click=on_click, on_move=on_move) as listener:
        listener.join()

    if cancelled:
        return None
    return pattern if done else None


def setup_pattern(config_dir) -> dict:
    """Configuration initiale"""
    print("\n  🔐 Configuration du schéma de déverrouillage\n")
    print("  La grille 3x3 correspond à votre écran :")
    print(GRID_DISPLAY)
    print("  💡 Conseil : glissez LENTEMENT pour que chaque")
    print("     point soit bien reconnu (150ms par zone)\n")
    time.sleep(1)

    while True:
        pattern = capture_pattern("✏️  Dessinez votre schéma :", min_points=3)

        if pattern is None:
            print("\n  ❌ Annulé. Recommencez.\n")
            continue

        print(f"\n  ✅ Schéma enregistré : {' → '.join(pattern)}")
        print(f"  ({len(pattern)} points)\n")
        time.sleep(0.8)

        print("  🔄 Confirmez en redessinant le même schéma :\n")
        time.sleep(0.5)

        confirm = capture_pattern("🔄 Confirmez :", min_points=3)

        if confirm is None:
            continue

        if pattern == confirm:
            print("\n  ✅ Schéma confirmé !\n")
            break
        else:
            print(f"\n  ❌ Différent !")
            print(f"  1er : {' → '.join(pattern)}")
            print(f"  2ème : {' → '.join(confirm)}")
            print(f"  Recommencez en glissant plus lentement.\n")
            time.sleep(1)

    # Délai
    while True:
        try:
            d = input("  ⏱️  Délai avant verrouillage (secondes) [10] : ").strip()
            delay = int(d) if d else 10
            if delay >= 1:
                break
            print("  ❌ Minimum 1 seconde\n")
        except ValueError:
            print("  ❌ Entrez un nombre\n")

    print(f"\n  ✅ Tout configuré ! Délai : {delay}s\n")

    return {
        "pattern_hash": _hash_pattern(pattern),
        "lock_delay_seconds": delay,
        "platform_lock": "auto",
        "log_path": str(config_dir / "fingerlock.log"),
    }


def verify_pattern(stored_hash: str, max_attempts: int = 3) -> bool:
    """Vérifie le schéma pour déverrouiller"""
    print("\n  🔒 Système verrouillé")
    print(GRID_DISPLAY)
    print("  Dessinez votre schéma pour déverrouiller\n")

    for attempt in range(1, max_attempts + 1):
        pattern = capture_pattern(
            f"Tentative {attempt}/{max_attempts} :",
            min_points=3
        )
        if pattern is None:
            continue
        if _hash_pattern(pattern) == stored_hash:
            print("\n  ✅ Déverrouillé !\n")
            return True
        remaining = max_attempts - attempt
        if remaining > 0:
            print(f"\n  ❌ Incorrect ! {remaining} tentative(s) restante(s).\n")
            time.sleep(0.5)
        else:
            print(f"\n  🚫 Trop de tentatives !\n")

    return False
