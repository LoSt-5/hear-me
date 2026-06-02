"""Карусель-туториал по возможностям приложения (Demo / Pro)."""
from __future__ import annotations

from typing import Literal

import customtkinter as ctk

Edition = Literal["demo", "pro"]

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_BODY = ("Segoe UI", 14)
FONT_SMALL = ("Segoe UI", 11)

ACCENT = {
    "demo": "#38BDF8",
    "pro": "#FBBF24",
}

SLIDES: dict[Edition, list[tuple[str, str]]] = {
    "demo": [
        (
            "Добро пожаловать",
            "«Жест ИИ» распознаёт русский жестовый язык в реальном времени "
            "через веб-камеру. Покажите жест перед камерой — слово появится справа.",
        ),
        (
            "Камера",
            "Слева — видео с камеры. Держите руки в кадре, при хорошем освещении "
            "распознавание стабильнее. Жест удерживайте около секунды.",
        ),
        (
            "Распознанный жест",
            "Крупная надпись справа — текущий жест. Пока модель не уверена, "
            "отображается «Ожидание жеста…».",
        ),
        (
            "Накопление кадров",
            "Полоска и счётчик (например, 0 / 32) показывают, сколько кадров набрано "
            "для одного предсказания. Когда полоска заполнится, жест обновится.",
        ),
        (
            "История",
            "Ниже — последние распознанные жесты в порядке показа. "
            "Удобно собирать короткую последовательность знаков.",
        ),
        (
            "Версия Demo",
            "В демо доступно только распознавание в реальном времени — без озвучки "
            "и без записи целой фразы.",
        ),
        (
            "PRO-возможности",
            "В PRO: озвучивание жестов, режим «Запись фразы» (клавиша R) "
            "и озвучка собранной фразы. Кнопка «Перейти на PRO» — в шапке окна.",
        ),
    ],
    "pro": [
        (
            "Добро пожаловать в PRO",
            "Полная версия: распознавание жестов, озвучка и запись фраз из "
            "нескольких жестов подряд.",
        ),
        (
            "Камера",
            "Слева — изображение с веб-камеры. Во время записи фразы в углу "
            "появляется индикатор REC.",
        ),
        (
            "Реальное время",
            "Режим по умолчанию: каждый удержанный жест сразу показывается справа. "
            "При включённом «Озвучивать» слово произносится вслух.",
        ),
        (
            "Запись фразы",
            "Переключите режим на «Запись фразы». Нажмите «Начать запись» или R — "
            "покажите серию жестов, снова R для остановки. Программа соберёт фразу.",
        ),
        (
            "Озвучивание",
            "Переключатель «Озвучивать»: в реальном времени — каждый новый жест; "
            "после записи — вся собранная фраза целиком.",
        ),
        (
            "Накопление и история",
            "Полоска кадров — готовность модели к предсказанию. "
            "«История» — последние жесты; после записи фразы подставляется цепочка из сессии.",
        ),
        (
            "Горячие клавиши",
            "R — начать или остановить запись (только в режиме «Запись фразы»). "
            "ESC — выход из программы. Удачной работы!",
        ),
    ],
}


class TutorialCarouselDialog(ctk.CTkToplevel):
    def __init__(self, master, edition: Edition = "demo"):
        super().__init__(master)
        self._slides = SLIDES[edition]
        self._index = 0
        self._accent = ACCENT[edition]

        self.title("Туториал")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(fg_color="#0B0F1A")
        self.transient(master)
        self.grab_set()

        pad = {"padx": 28, "pady": 8}

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 0))

        self._step_label = ctk.CTkLabel(
            top,
            text="",
            font=FONT_SMALL,
            text_color="#64748B",
        )
        self._step_label.pack(side="left")

        ctk.CTkButton(
            top,
            text="✕",
            width=32,
            height=32,
            font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#1E293B",
            text_color="#94A3B8",
            command=self.destroy,
        ).pack(side="right")

        self._card = ctk.CTkFrame(self, fg_color="#151B2E", corner_radius=16)
        self._card.pack(fill="both", expand=True, padx=28, pady=(12, 8))

        self._title_label = ctk.CTkLabel(
            self._card,
            text="",
            font=FONT_TITLE,
            text_color=self._accent,
            wraplength=440,
            justify="left",
        )
        self._title_label.pack(anchor="w", padx=24, pady=(24, 12))

        self._body_label = ctk.CTkLabel(
            self._card,
            text="",
            font=FONT_BODY,
            text_color="#CBD5E1",
            wraplength=440,
            justify="left",
        )
        self._body_label.pack(anchor="w", padx=24, pady=(0, 24))

        self._dots_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._dots_frame.pack(pady=(4, 8))
        self._dot_labels: list[ctk.CTkLabel] = []
        for i in range(len(self._slides)):
            dot = ctk.CTkLabel(
                self._dots_frame,
                text="●",
                font=("Segoe UI", 10),
                text_color="#334155",
                width=20,
            )
            dot.pack(side="left", padx=2)
            self._dot_labels.append(dot)

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=28, pady=(0, 24))

        self._back_btn = ctk.CTkButton(
            nav,
            text="Назад",
            font=("Segoe UI", 13),
            width=100,
            fg_color="#334155",
            hover_color="#475569",
            command=self._prev,
        )
        self._back_btn.pack(side="left")

        self._next_btn = ctk.CTkButton(
            nav,
            text="Далее",
            font=("Segoe UI", 13, "bold"),
            width=120,
            fg_color=self._accent,
            hover_color="#0EA5E9" if edition == "demo" else "#D97706",
            text_color="#0B0F1A",
            command=self._next,
        )
        self._next_btn.pack(side="right")

        self._show_slide(0)
        self._center_on_master(master)

    def _center_on_master(self, master) -> None:
        self.update_idletasks()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = master.winfo_width()
        mh = master.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = mx + (mw - w) // 2
        y = my + (mh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _show_slide(self, index: int) -> None:
        self._index = index
        title, body = self._slides[index]
        total = len(self._slides)

        self._step_label.configure(text=f"Шаг {index + 1} из {total}")
        self._title_label.configure(text=title)
        self._body_label.configure(text=body)

        for i, dot in enumerate(self._dot_labels):
            dot.configure(text_color=self._accent if i == index else "#334155")

        self._back_btn.configure(state="disabled" if index == 0 else "normal")
        if index == total - 1:
            self._next_btn.configure(text="Готово", command=self.destroy)
        else:
            self._next_btn.configure(text="Далее", command=self._next)

    def _prev(self) -> None:
        if self._index > 0:
            self._show_slide(self._index - 1)

    def _next(self) -> None:
        if self._index < len(self._slides) - 1:
            self._show_slide(self._index + 1)
        else:
            self.destroy()


def open_tutorial(master, edition: Edition = "demo") -> None:
    TutorialCarouselDialog(master, edition=edition)
