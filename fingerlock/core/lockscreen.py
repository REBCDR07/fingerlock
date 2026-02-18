"""FingerLock – Lock screen premium"""
import tkinter as tk
import hashlib
import math
import os
from typing import List
from datetime import datetime

GRID_SIZE     = 3
POINT_RADIUS  = 26
POINT_SPACING = 110  # Réduit de 150 à 110
VALIDATE_BTN_W = 150
VALIDATE_BTN_H = 48

# Palette
COLOR_BG1     = "#0f0c29"
COLOR_BG2     = "#302b63"
COLOR_RING    = "#2d2d44"
COLOR_ACTIVE  = "#ff6b9d"
COLOR_LINE    = "#ff6b9d"
COLOR_SUCCESS = "#06ffa5"
COLOR_ERROR   = "#ff3864"
COLOR_TEXT    = "#ffffff"
COLOR_SUBTEXT = "#a0a0c0"
COLOR_TIME    = "#e0e0ff"
COLOR_CONFIRM = "#06ffa5"
COLOR_SHADOW  = "#1a1a2e"

BANNER = """ _____ _                       _                _    
|  ___(_)_ __   __ _  ___ _ __| |    ___   ___| | __
| |_  | | '_ \\ / _` |/ _ \\ '__| |   / _ \\ / __| |/ /
|  _| | | | | | (_| |  __/ |  | |__| (_) | (__|   < 
|_|   |_|_| |_|\\__, |\\___|_|  |_____\\___/ \\___|_|\\_\\
               |___/"""

POINT_LABELS = {1:'1', 2:'2', 3:'3', 4:'4', 5:'5',
                6:'6', 7:'7', 8:'8', 9:'9'}

def _hash(pattern: List[int]) -> str:
    return hashlib.sha256("-".join(str(p) for p in pattern).encode()).hexdigest()

def _dist(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def _play_sound(sound_type: str):
    try:
        if os.name == 'posix':
            sounds = {
                'point': '/usr/share/sounds/freedesktop/stereo/message.oga',
                'error': '/usr/share/sounds/freedesktop/stereo/dialog-error.oga',
                'success': '/usr/share/sounds/freedesktop/stereo/complete.oga'
            }
            if sound_type in sounds:
                os.system(f'paplay {sounds[sound_type]} 2>/dev/null &')
    except: pass


class LockScreen:
    def __init__(self, stored_hash: str, max_attempts: int = 3, setup_mode: bool = False):
        self.stored_hash    = stored_hash
        self.max_attempts   = max_attempts
        self.setup_mode     = setup_mode
        self.pattern        = []
        self.tracking       = False
        self.attempt        = 1
        self.unlocked       = False
        self.result_pattern = None
        self.pulse_phase    = 0
        self.line_progress  = []

        self.root = tk.Tk()
        self.root.title("FingerLock")
        self.root.configure(bg=COLOR_BG1)
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()

        total = POINT_SPACING * (GRID_SIZE - 1)
        self.grid_ox = (self.sw - total) // 2
        self.grid_oy = int(self.sh * 0.54)  # Un peu plus bas

        self.positions = {}
        idx = 1
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = self.grid_ox + col * POINT_SPACING
                y = self.grid_oy + row * POINT_SPACING
                self.positions[idx] = (x, y)
                idx += 1

        confirm_y = self.grid_oy + total + 75
        self.confirm_zone = (
            self.sw // 2 - VALIDATE_BTN_W // 2, confirm_y,
            self.sw // 2 + VALIDATE_BTN_W // 2, confirm_y + VALIDATE_BTN_H
        )

        self.canvas = tk.Canvas(self.root, width=self.sw, height=self.sh,
                                bg=COLOR_BG1, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.time_var   = tk.StringVar()
        self.date_var   = tk.StringVar()
        self.status_var = tk.StringVar(value="Glissez votre schéma")
        self.msg_var    = tk.StringVar(value="")

        self.canvas.bind("<Motion>", self._on_motion)
        self._update_time()
        self._animate()

    def _update_time(self):
        now = datetime.now()
        self.time_var.set(now.strftime("%H:%M:%S"))
        self.date_var.set(now.strftime("%A %d %B %Y"))
        self.root.after(1000, self._update_time)

    def _animate(self):
        self.pulse_phase = (self.pulse_phase + 0.08) % (2 * math.pi)
        for i in range(len(self.line_progress)):
            if self.line_progress[i] < 1.0:
                self.line_progress[i] = min(1.0, self.line_progress[i] + 0.15)
        self._draw()
        self.root.after(50, self._animate)

    def _draw(self, state="normal", mx=None, my=None):
        self.canvas.delete("all")
        sw, sh = self.sw, self.sh

        # Dégradé
        self._draw_gradient()

        # Horloge (plus haut)
        self.canvas.create_text(sw // 2, 70,
                                 text=self.time_var.get(),
                                 fill=COLOR_TIME,
                                 font=("Helvetica", 52, "bold"))
        self.canvas.create_text(sw // 2, 115,
                                 text=self.date_var.get(),
                                 fill=COLOR_SUBTEXT,
                                 font=("Helvetica", 15))

        # Logo (plus haut et plus petit)
        y_logo = 160
        for i, line in enumerate(BANNER.split("\n")):
            self.canvas.create_text(sw // 2, y_logo + i * 14,
                                    text=line, fill=COLOR_ACTIVE,
                                    font=("Courier", 8, "bold"))

        # Titre (plus haut)
        self.canvas.create_text(sw // 2, int(sh * 0.36),
                                 text="🔒  Système verrouillé" if not self.setup_mode else "🎨  Configuration",
                                 fill=COLOR_TEXT,
                                 font=("Helvetica", 22, "bold"))

        # Schéma actuel (une seule ligne)
        if self.pattern:
            schema_txt = " → ".join(str(p) for p in self.pattern)
            self.canvas.create_text(sw // 2, int(sh * 0.41),
                                     text=schema_txt,
                                     fill=COLOR_ACTIVE,
                                     font=("Helvetica", 16, "bold"))

        # Statut (réduit l'espace)
        self.canvas.create_text(sw // 2, int(sh * 0.45),
                                 text=self.status_var.get(),
                                 fill=COLOR_SUBTEXT,
                                 font=("Helvetica", 12))

        # Tentatives (uniquement en mode vérif)
        if not self.setup_mode:
            self.canvas.create_text(sw // 2, int(sh * 0.48),
                                     text=f"Tentative {self.attempt}/{self.max_attempts}",
                                     fill=COLOR_SUBTEXT,
                                     font=("Helvetica", 10))

        # Lignes progressives
        line_color = COLOR_SUCCESS if state == "success" else \
                     COLOR_ERROR if state == "error" else COLOR_LINE

        for i in range(len(self.pattern) - 1):
            if i < len(self.line_progress):
                progress = self.line_progress[i]
                x1, y1 = self.positions[self.pattern[i]]
                x2, y2 = self.positions[self.pattern[i + 1]]
                
                draw_x2 = x1 + (x2 - x1) * progress
                draw_y2 = y1 + (y2 - y1) * progress
                
                self.canvas.create_line(x1+2, y1+2, draw_x2+2, draw_y2+2,
                                        fill=COLOR_SHADOW, width=4, smooth=True)
                self.canvas.create_line(x1, y1, draw_x2, draw_y2,
                                        fill=line_color, width=3, smooth=True)

        if self.tracking and mx and my and self.pattern:
            lx, ly = self.positions[self.pattern[-1]]
            self.canvas.create_line(lx, ly, mx, my,
                                    fill=line_color, width=2, dash=(6, 3))

        # Points avec pulse
        pulse_scale = 1 + 0.12 * math.sin(self.pulse_phase)
        
        for idx, (x, y) in self.positions.items():
            active = idx in self.pattern
            ring = COLOR_ACTIVE if active else COLOR_RING
            if state == "success": ring = COLOR_SUCCESS
            if state == "error": ring = COLOR_ERROR

            if active:
                glow_r = POINT_RADIUS * pulse_scale * 1.25
                self.canvas.create_oval(x - glow_r, y - glow_r,
                                        x + glow_r, y + glow_r,
                                        outline=ring, width=1)

            self.canvas.create_oval(
                x - POINT_RADIUS + 2, y - POINT_RADIUS + 2,
                x + POINT_RADIUS + 2, y + POINT_RADIUS + 2,
                outline="", fill=COLOR_SHADOW)

            r = POINT_RADIUS * (pulse_scale if active else 1.0)
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    outline=ring, width=2, fill=COLOR_BG2)

            if active:
                inner = r * 0.5
                fill = COLOR_SUCCESS if state == "success" else \
                       COLOR_ERROR if state == "error" else COLOR_ACTIVE
                self.canvas.create_oval(x - inner, y - inner,
                                        x + inner, y + inner,
                                        fill=fill, outline="")

            label_color = COLOR_TEXT if active else COLOR_SUBTEXT
            self.canvas.create_text(x, y, text=POINT_LABELS[idx],
                                    fill=label_color,
                                    font=("Helvetica", 12, "bold"))

        # Bouton Valider
        x1, y1, x2, y2 = self.confirm_zone
        if len(self.pattern) >= 3:
            btn_color = COLOR_SUCCESS if state == "success" else COLOR_CONFIRM
            self.canvas.create_rectangle(x1+2, y1+2, x2+2, y2+2,
                                         fill=COLOR_SHADOW, outline="")
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         fill=btn_color, outline="")
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                    text="✅  Valider",
                                    fill="#000000",
                                    font=("Helvetica", 13, "bold"))
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         fill=COLOR_RING, outline="")
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                    text="Min. 3 points",
                                    fill=COLOR_SUBTEXT,
                                    font=("Helvetica", 11))

        # Message (en dessous du bouton)
        msg = self.msg_var.get()
        if msg:
            color = COLOR_SUCCESS if state == "success" else COLOR_ERROR
            self.canvas.create_text(sw // 2, y2 + 35,
                                    text=msg, fill=color,
                                    font=("Helvetica", 13, "bold"))

    def _draw_gradient(self):
        steps = 60
        for i in range(steps):
            ratio = i / steps
            r = int((1-ratio) * int(COLOR_BG1[1:3], 16) + ratio * int(COLOR_BG2[1:3], 16))
            g = int((1-ratio) * int(COLOR_BG1[3:5], 16) + ratio * int(COLOR_BG2[3:5], 16))
            b = int((1-ratio) * int(COLOR_BG1[5:7], 16) + ratio * int(COLOR_BG2[5:7], 16))
            color = f"#{r:02x}{g:02x}{b:02x}"
            y1 = int(i * self.sh / steps)
            y2 = int((i + 1) * self.sh / steps)
            self.canvas.create_rectangle(0, y1, self.sw, y2, fill=color, outline="")

    def _in_confirm_zone(self, x, y):
        x1, y1, x2, y2 = self.confirm_zone
        return x1 <= x <= x2 and y1 <= y <= y2

    def _in_grid_zone(self, x, y):
        total = POINT_SPACING * (GRID_SIZE - 1)
        return (self.grid_ox - 70 <= x <= self.grid_ox + total + 70 and
                self.grid_oy - 70 <= y <= self.grid_oy + total + 70)

    def _get_point(self, x, y):
        for idx, (px, py) in self.positions.items():
            if _dist(x, y, px, py) <= POINT_RADIUS + 16:
                return idx
        return None

    def _on_motion(self, e):
        x, y = e.x, e.y

        # Validation
        if self._in_confirm_zone(x, y) and len(self.pattern) >= 3:
            self._validate()
            return

        # Tracé
        if self._in_grid_zone(x, y):
            if not self.tracking:
                self.tracking = True
                self.pattern = []
                self.line_progress = []
                self.msg_var.set("")

            pt = self._get_point(x, y)
            if pt and pt not in self.pattern:
                self.pattern.append(pt)
                self.line_progress.append(0.0)
                _play_sound('point')
                self.status_var.set("Passez sur ✅ pour valider")
        else:
            self.tracking = False

    def _validate(self):
        self.tracking = False
        if len(self.pattern) < 3:
            _play_sound('error')
            self.msg_var.set("❌ Minimum 3 points")
            self.root.after(700, self._reset)
            return

        # Mode setup : retourner le pattern
        if self.setup_mode:
            _play_sound('success')
            self.result_pattern = self.pattern.copy()
            self.msg_var.set("✅ Schéma enregistré !")
            self.root.after(500, self.root.destroy)
            return

        # Mode vérification
        if _hash(self.pattern) == self.stored_hash:
            _play_sound('success')
            code = "".join(str(p) for p in self.pattern)
            self.msg_var.set(f"✅ Code {code} correct !")
            self.unlocked = True
            self.root.after(700, self.root.destroy)
        else:
            _play_sound('error')
            remaining = self.max_attempts - self.attempt
            self.msg_var.set(f"❌ Incorrect — {remaining} restante(s)")
            self.attempt += 1
            if self.attempt > self.max_attempts:
                self.root.after(1200, self.root.destroy)
            else:
                self.root.after(1000, self._reset)

    def _reset(self):
        self.pattern = []
        self.line_progress = []
        self.tracking = False
        self.msg_var.set("")
        self.status_var.set("Glissez votre schéma")

    def show(self):
        self.root.mainloop()
        return self.unlocked

    def get_drawn_pattern(self):
        self.root.mainloop()
        return self.result_pattern


def show_lockscreen(stored_hash: str) -> bool:
    screen = LockScreen(stored_hash, max_attempts=3, setup_mode=False)
    return screen.show()

def draw_pattern_screen(title: str = "") -> List[int]:
    screen = LockScreen("", max_attempts=1, setup_mode=True)
    return screen.get_drawn_pattern()
