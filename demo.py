"""
Демо-версия: тёмный интерфейс CustomTkinter + камера + распознавание жестов.
Только режим реального времени, без озвучки и записи фраз.
Запуск: python demo.py
"""
import sys
from collections import deque

import customtkinter as ctk
import cv2
from PIL import Image

from services.tutorial_dialog import open_tutorial
from services.upgrade_dialog import UpgradeProDialog
from utils import DEFAULT_CONFIG, SLInference

IGNORE = {"", "no"}

# Шрифты с кириллицей
FONT_UI = ("Segoe UI", 13)
FONT_GESTURE = ("Segoe UI", 36, "bold")
FONT_SMALL = ("Segoe UI", 11)

COLORS = {
    "accent": "#38BDF8",
    "badge": "#0EA5E9",
}


class GestureDemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Жест ИИ — Demo")
        self.geometry("1120x760")
        self.minsize(960, 640)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.inference = SLInference(DEFAULT_CONFIG)
        self.inference.start()

        self.history: deque[str] = deque(maxlen=8)
        self._photo_ref = None
        self._running = True

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.destroy()
            raise SystemExit("Не удалось открыть веб-камеру.")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(30, self._tick)

    def _build_ui(self) -> None:
        self.configure(fg_color="#0B0F1A")

        header = ctk.CTkFrame(self, fg_color="#12182B", corner_radius=0, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        badge = ctk.CTkLabel(
            header,
            text="DEMO",
            font=("Segoe UI", 12, "bold"),
            text_color="#0B0F1A",
            fg_color=COLORS["badge"],
            corner_radius=8,
            width=56,
            height=28,
        )
        badge.pack(side="left", padx=(20, 12), pady=20)

        ctk.CTkLabel(
            header,
            text="Распознавание русского жестового языка",
            font=("Segoe UI", 18, "bold"),
            text_color="#E2E8F0",
        ).pack(side="left", pady=20)

        ctk.CTkButton(
            header,
            text="Перейти на PRO",
            font=("Segoe UI", 12, "bold"),
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="#0B0F1A",
            corner_radius=8,
            height=32,
            command=self._open_upgrade,
        ).pack(side="right", padx=(8, 12), pady=20)

        ctk.CTkButton(
            header,
            text="Туториал",
            font=("Segoe UI", 12),
            fg_color="#334155",
            hover_color="#475569",
            corner_radius=8,
            height=32,
            command=lambda: open_tutorial(self, edition="demo"),
        ).pack(side="right", padx=(0, 8), pady=20)

        ctk.CTkLabel(
            header,
            text="ESC — выход",
            font=FONT_SMALL,
            text_color="#64748B",
        ).pack(side="right", padx=(0, 8))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(12, 20))

        left = ctk.CTkFrame(body, fg_color="#151B2E", corner_radius=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            left,
            text="Камера",
            font=("Segoe UI", 14, "bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        self.video_label = ctk.CTkLabel(left, text="", fg_color="#0B0F1A", corner_radius=12)
        self.video_label.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        right = ctk.CTkFrame(body, fg_color="#151B2E", corner_radius=16, width=400)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        pad = {"padx": 20, "pady": 8}

        ctk.CTkLabel(
            right,
            text="Распознанный жест",
            font=("Segoe UI", 12, "bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", **pad)

        self.gesture_label = ctk.CTkLabel(
            right,
            text="Ожидание жеста…",
            font=FONT_GESTURE,
            text_color=COLORS["accent"],
            wraplength=340,
            justify="left",
        )
        self.gesture_label.pack(anchor="w", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            right,
            text="Накопление кадров",
            font=FONT_SMALL,
            text_color="#64748B",
        ).pack(anchor="w", padx=20)

        self.buffer_bar = ctk.CTkProgressBar(
            right, height=10, corner_radius=6, progress_color=COLORS["accent"]
        )
        self.buffer_bar.pack(fill="x", padx=20, pady=(4, 4))
        self.buffer_bar.set(0)

        self.buffer_label = ctk.CTkLabel(
            right, text="0 / 32", font=FONT_SMALL, text_color="#94A3B8"
        )
        self.buffer_label.pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            right,
            text="История",
            font=("Segoe UI", 12, "bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=20, pady=(8, 4))

        self.history_label = ctk.CTkLabel(
            right,
            text="—",
            font=FONT_UI,
            text_color="#CBD5E1",
            wraplength=340,
            justify="left",
        )
        self.history_label.pack(anchor="w", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            right,
            text="Покажите жест перед камерой и удерживайте ~1 секунду.",
            font=FONT_SMALL,
            text_color="#475569",
            justify="left",
        ).pack(side="bottom", anchor="w", padx=20, pady=16)

        self.bind("<Escape>", lambda _e: self._on_close())

    def _open_upgrade(self) -> None:
        UpgradeProDialog(self, on_activated=self._switch_to_pro)

    def _switch_to_pro(self) -> None:
        self._running = False
        self.inference.stop()
        self.cap.release()
        self.withdraw()
        self.destroy()
        from pro import GestureProApp

        app = GestureProApp()
        app.mainloop()

    def _tick(self) -> None:
        if not self._running:
            return

        ok, frame = self.cap.read()
        if ok:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small = cv2.resize(rgb, (224, 224))

            # Отправляем в очередь для инференса
            self.inference.input_queue.append(small)

            display = cv2.resize(rgb, (640, 480))
            pil = Image.fromarray(display)
            ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(640, 480))
            self.video_label.configure(image=ctk_img)
            self._photo_ref = ctk_img

        self._update_results()

        if self._running:
            self.after(33, self._tick)

    def _update_results(self) -> None:
        gesture = self.inference.pred
        need = self.inference.config["window_size"]
        filled = len(self.inference.input_queue)

        self.buffer_bar.set(min(filled / need, 1.0))
        self.buffer_label.configure(text=f"{filled} / {need}")

        if gesture and gesture not in IGNORE:
            if not self.history or self.history[-1] != gesture:
                self.history.append(gesture)
            self.gesture_label.configure(text=gesture, text_color=COLORS["accent"])
        else:
            self.gesture_label.configure(text="Ожидание жеста…", text_color="#64748B")

        self._refresh_history()

    def _refresh_history(self) -> None:
        if self.history:
            self.history_label.configure(text="  →  ".join(self.history))
        else:
            self.history_label.configure(text="Пока пусто")

    def _on_close(self) -> None:
        self._running = False
        self.inference.stop()
        self.cap.release()
        self.destroy()


def main() -> None:
    try:
        app = GestureDemoApp()
        app.mainloop()
    except SystemExit as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()