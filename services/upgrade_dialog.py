"""Окно «Перейти на PRO»: оплата в браузере и активация ключа."""
from __future__ import annotations

import webbrowser
from typing import Callable

import customtkinter as ctk

from services.licensing import activate_license, load_commerce_config

FONT_UI = ("Segoe UI", 13)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SMALL = ("Segoe UI", 11)

PRO_FEATURES = (
    "Озвучивание распознанных жестов",
    "Режим записи фразы (клавиша R)",
    "Сборка и озвучка целой фразы",
)


class UpgradeProDialog(ctk.CTkToplevel):
    def __init__(self, master, on_activated: Callable[[], None] | None = None):
        super().__init__(master)
        self._on_activated = on_activated
        self._commerce = load_commerce_config()

        self.title("Перейти на PRO")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(fg_color="#0B0F1A")
        self.transient(master)
        self.grab_set()

        pad = {"padx": 24, "pady": 6}

        ctk.CTkLabel(
            self,
            text="Жест ИИ — PRO",
            font=FONT_TITLE,
            text_color="#FBBF24",
        ).pack(anchor="w", **pad)

        price = self._commerce.get("price_rub")
        price_text = f"Разовая покупка — {price} ₽" if price else "Разовая покупка"
        ctk.CTkLabel(
            self,
            text=price_text,
            font=FONT_UI,
            text_color="#94A3B8",
        ).pack(anchor="w", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            self,
            text="В PRO входит:",
            font=("Segoe UI", 12, "bold"),
            text_color="#E2E8F0",
        ).pack(anchor="w", **pad)

        for feat in PRO_FEATURES:
            ctk.CTkLabel(
                self,
                text=f"  •  {feat}",
                font=FONT_UI,
                text_color="#CBD5E1",
                justify="left",
            ).pack(anchor="w", padx=24, pady=2)

        ctk.CTkFrame(self, fg_color="#1E293B", height=1).pack(fill="x", padx=24, pady=16)

        ctk.CTkLabel(
            self,
            text="1. Оплатите на сайте\n2. Скопируйте ключ из письма или личного кабинета\n3. Вставьте ключ ниже",
            font=FONT_SMALL,
            text_color="#64748B",
            justify="left",
        ).pack(anchor="w", **pad)

        pay_row = ctk.CTkFrame(self, fg_color="transparent")
        pay_row.pack(fill="x", padx=24, pady=(8, 4))

        payment_url = (self._commerce.get("payment_url") or "").strip()
        ctk.CTkButton(
            pay_row,
            text="Оплатить",
            font=FONT_UI,
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="#0B0F1A",
            command=self._open_payment,
            state="normal" if payment_url else "disabled",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        support = (self._commerce.get("support_email") or "").strip()
        if support:
            ctk.CTkButton(
                pay_row,
                text="Поддержка",
                font=FONT_UI,
                fg_color="#334155",
                hover_color="#475569",
                width=110,
                command=lambda: webbrowser.open(f"mailto:{support}"),
            ).pack(side="right")

        if not payment_url:
            ctk.CTkLabel(
                self,
                text="Укажите payment_url в configs/commerce.json",
                font=FONT_SMALL,
                text_color="#EF4444",
            ).pack(anchor="w", padx=24)

        self.key_entry = ctk.CTkEntry(
            self,
            placeholder_text="HM-XXXX-XXXX-XXXX-XXXX",
            font=FONT_UI,
            height=40,
        )
        self.key_entry.pack(fill="x", padx=24, pady=(12, 4))

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=FONT_SMALL,
            text_color="#94A3B8",
            wraplength=420,
            justify="left",
        )
        self.status_label.pack(anchor="w", padx=24, pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(12, 24))

        ctk.CTkButton(
            btn_row,
            text="Активировать PRO",
            font=FONT_UI,
            fg_color="#38BDF8",
            hover_color="#0EA5E9",
            command=self._try_activate,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Закрыть",
            font=FONT_UI,
            fg_color="#334155",
            hover_color="#475569",
            width=100,
            command=self.destroy,
        ).pack(side="right")

        self.key_entry.bind("<Return>", lambda _e: self._try_activate())
        self.after(100, self.key_entry.focus_set)

    def _open_payment(self) -> None:
        url = (self._commerce.get("payment_url") or "").strip()
        if url:
            webbrowser.open(url)

    def _try_activate(self) -> None:
        key = self.key_entry.get().strip()
        if not key:
            self.status_label.configure(
                text="Введите лицензионный ключ.",
                text_color="#F87171",
            )
            return

        ok, message = activate_license(key)
        if ok:
            self.status_label.configure(text=message, text_color="#4ADE80")
            self.after(400, self._finish_success)
        else:
            self.status_label.configure(text=message, text_color="#F87171")

    def _finish_success(self) -> None:
        self.grab_release()
        self.destroy()
        if self._on_activated:
            self._on_activated()
