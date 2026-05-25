"""
Pro-версия: тёмный интерфейс CustomTkinter + камера + распознавание.
Поддерживает:
- Реальное время с озвучкой жестов
- Запись фразы (R) и её озвучивание
Запуск: python pro.py
"""
import sys
from collections import deque
from threading import Thread

import customtkinter as ctk
import cv2
from PIL import Image

from utils import DEFAULT_CONFIG, SLInference
from services.tts import SpeechEngine
from services.phrase_recording import build_phrase, scan_frames

IGNORE = {"", "no"}

# Шрифты с кириллицей
FONT_UI = ("Segoe UI", 13)
FONT_TITLE = ("Segoe UI", 28, "bold")
FONT_GESTURE = ("Segoe UI", 36, "bold")
FONT_SMALL = ("Segoe UI", 11)

COLORS = {
    "pro": {"accent": "#FBBF24", "badge": "#F59E0B"},
    "record": "#EF4444",
}


class GestureProApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Жест ИИ — Pro")
        self.geometry("1120x760")
        self.minsize(960, 640)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.inference = SLInference(DEFAULT_CONFIG)
        self.inference.start()

        self.speech = SpeechEngine()
        self.tts_enabled = ctk.BooleanVar(value=True)
        self.last_spoken = ""
        self.work_mode = ctk.StringVar(value="Реальное время")
        self.recording = False
        self.processing = False
        self.record_frames: list = []
        self.last_phrase = ""

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
            text="PRO",
            font=("Segoe UI", 12, "bold"),
            text_color="#0B0F1A",
            fg_color=COLORS["pro"]["badge"],
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

        self.record_badge = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color="#FFF",
            fg_color=COLORS["record"],
            corner_radius=8,
            width=120,
            height=28,
        )

        ctk.CTkLabel(
            header,
            text="R — запись · ESC — выход",
            font=FONT_SMALL,
            text_color="#64748B",
        ).pack(side="right", padx=20)

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
            text="Режим Pro",
            font=("Segoe UI", 12, "bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", **pad)

        mode_row = ctk.CTkFrame(right, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkSegmentedButton(
            mode_row,
            values=["Реальное время", "Запись фразы"],
            variable=self.work_mode,
            font=FONT_UI,
            command=self._on_work_mode_change,
        ).pack(fill="x")
        ctk.CTkLabel(
            right,
            text="В реальном времени — жесты сразу. Запись фразы — R, затем обработка.",
            font=FONT_SMALL,
            text_color="#64748B",
            wraplength=340,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        rec_row = ctk.CTkFrame(right, fg_color="transparent")
        rec_row.pack(fill="x", padx=20, pady=(0, 8))
        self.record_btn = ctk.CTkButton(
            rec_row,
            text="● Начать запись (R)",
            font=FONT_UI,
            fg_color="#334155",
            hover_color="#475569",
            command=self._toggle_recording,
        )
        self.record_btn.pack(fill="x")

        self.phrase_label = ctk.CTkLabel(
            right,
            text="Фраза появится после остановки записи",
            font=FONT_UI,
            text_color="#94A3B8",
            wraplength=340,
            justify="left",
        )
        self.phrase_label.pack(anchor="w", padx=20, pady=(0, 12))

        ctk.CTkFrame(right, fg_color="#1E293B", height=1).pack(fill="x", padx=20, pady=4)

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
            text_color=COLORS["pro"]["accent"],
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
            right, height=10, corner_radius=6, progress_color=COLORS["pro"]["accent"]
        )
        self.buffer_bar.pack(fill="x", padx=20, pady=(4, 4))
        self.buffer_bar.set(0)

        self.buffer_label = ctk.CTkLabel(
            right, text="0 / 32", font=FONT_SMALL, text_color="#94A3B8"
        )
        self.buffer_label.pack(anchor="w", padx=20, pady=(0, 16))

        tts_row = ctk.CTkFrame(right, fg_color="transparent")
        tts_row.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkSwitch(
            tts_row,
            text="Озвучивать",
            variable=self.tts_enabled,
            font=FONT_UI,
            progress_color=COLORS["pro"]["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            right,
            text="В реальном времени — каждый жест. После записи — вся фраза.",
            font=FONT_SMALL,
            text_color="#64748B",
            wraplength=340,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

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
            text="Реальное время: жесты сразу на экране.\nЗапись фразы: R — старт/стоп, затем скан и озвучка.",
            font=FONT_SMALL,
            text_color="#475569",
            justify="left",
        ).pack(side="bottom", anchor="w", padx=20, pady=16)

        self.bind("<Escape>", lambda _e: self._on_close())
        self.bind("<KeyPress-r>", self._on_hotkey_record)
        self.bind("<KeyPress-R>", self._on_hotkey_record)
        self._on_work_mode_change()

    def _phrase_mode(self) -> bool:
        return self.work_mode.get() == "Запись фразы"

    def _on_work_mode_change(self, _value: str | None = None) -> None:
        phrase_mode = self._phrase_mode()
        state = "normal" if phrase_mode and not self.processing else "disabled"
        self.record_btn.configure(state=state)
        if not phrase_mode and self.recording:
            self._stop_recording()

    def _on_hotkey_record(self, event) -> None:
        if not self._phrase_mode():
            return
        if event.widget and isinstance(event.widget, ctk.CTkEntry):
            return
        self._toggle_recording()

    def _toggle_recording(self) -> None:
        if not self._phrase_mode() or self.processing:
            return
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self.recording = True
        self.record_frames = []
        self.last_phrase = ""
        self.phrase_label.configure(
            text="Идёт запись… покажите жесты, затем R или «Остановить»",
            text_color=COLORS["record"],
        )
        self._update_record_ui()

    def _stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        self._update_record_ui()
        frames = list(self.record_frames)
        self.record_frames = []
        if not frames:
            self.phrase_label.configure(
                text="Запись пуста — покажите жесты перед остановкой",
                text_color="#64748B",
            )
            return

        self.processing = True
        self.record_btn.configure(state="disabled")
        self.phrase_label.configure(
            text="Обработка: сканирую кадры и собираю фразу…",
            text_color="#94A3B8",
        )
        Thread(target=self._process_recording_bg, args=(frames,), daemon=True).start()

    def _process_recording_bg(self, frames: list) -> None:
        gestures = scan_frames(frames, self.inference)
        phrase = build_phrase(gestures)
        self.after(0, lambda: self._on_phrase_ready(phrase, gestures))

    def _on_phrase_ready(self, phrase: str, gestures: list[str]) -> None:
        self.processing = False
        self.last_phrase = phrase
        self._on_work_mode_change()

        if phrase:
            self.history.clear()
            self.history.extend(gestures[-8:])
            self.phrase_label.configure(text=phrase, text_color=COLORS["pro"]["accent"])
            self.gesture_label.configure(text=phrase[:80] + ("…" if len(phrase) > 80 else ""))
            if self.tts_enabled.get():
                self.speech.speak(phrase)
                self.last_spoken = phrase
        else:
            self.phrase_label.configure(
                text="Жесты не распознаны — попробуйте дольше удерживать каждый жест",
                text_color="#64748B",
            )

        self._refresh_history()

    def _update_record_ui(self) -> None:
        if self.recording:
            self.record_badge.configure(text="● ЗАПИСЬ")
            self.record_badge.pack(side="right", padx=(0, 8), pady=20)
            self.record_btn.configure(
                text="■ Остановить и обработать (R)",
                fg_color=COLORS["record"],
                hover_color="#DC2626",
            )
            self.title("Жест ИИ — Pro [ЗАПИСЬ]")
        else:
            self.record_badge.pack_forget()
            self.record_btn.configure(
                text="● Начать запись (R)",
                fg_color="#334155",
                hover_color="#475569",
            )
            if not self.processing:
                self.title("Жест ИИ — Pro")

    def _tick(self) -> None:
        if not self._running:
            return

        ok, frame = self.cap.read()
        if ok:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small = cv2.resize(rgb, (224, 224))

            phrase_mode = self._phrase_mode()
            live_mode = not phrase_mode or self.recording

            if live_mode:
                self.inference.input_queue.append(small)
            if self.recording:
                self.record_frames.append(small.copy())

            display = cv2.resize(rgb, (640, 480))
            if self.recording:
                cv2.circle(display, (24, 24), 10, (239, 68, 68), -1)
                cv2.putText(
                    display,
                    "REC",
                    (42, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (239, 68, 68),
                    2,
                    cv2.LINE_AA,
                )

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

        phrase_mode = self._phrase_mode()
        allow_live_tts = not phrase_mode and self.tts_enabled.get()

        if gesture not in IGNORE:
            if not self.history or self.history[-1] != gesture:
                if not phrase_mode or self.recording:
                    self.history.append(gesture)
                if allow_live_tts and gesture != self.last_spoken:
                    self.speech.speak(gesture)
                    self.last_spoken = gesture

        if self.processing:
            self.gesture_label.configure(text="Обработка…", text_color="#94A3B8")
        elif self.recording:
            n = len(self.record_frames)
            self.gesture_label.configure(
                text=gesture if gesture else f"Запись… {n} кадров",
                text_color=COLORS["record"] if not gesture else COLORS["pro"]["accent"],
            )
        elif gesture:
            self.gesture_label.configure(text=gesture, text_color=COLORS["pro"]["accent"])
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
        self.speech.stop()
        self.cap.release()
        self.destroy()


def main() -> None:
    try:
        app = GestureProApp()
        app.mainloop()
    except SystemExit as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()