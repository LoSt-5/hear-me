"""
Снимает скриншоты окон для README (без реальной камеры и без ONNX-инференса).

Перед запуском сверните или закройте окна поверх рабочего стола.
На Windows используется PrintWindow — захват идёт с самого окна, а не с экрана.

Запуск из корня репозитория:
    python tools/capture_readme_screenshots.py
"""
from __future__ import annotations

import sys
import time
from collections import deque
from pathlib import Path

import cv2
import customtkinter as ctk
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "doc" / "screenshots"
COUNTDOWN_SEC = 3
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _placeholder_bgr(width: int = 640, height: int = 480) -> np.ndarray:
    frame = np.full((height, width, 3), (18, 24, 40), dtype=np.uint8)
    cx, cy = width // 2, height // 2
    y, x = np.ogrid[:height, :width]
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    glow = np.clip(1.0 - dist / (min(width, height) * 0.55), 0, 1)
    frame[:, :, 0] = (frame[:, :, 0] + glow * 35).astype(np.uint8)
    frame[:, :, 1] = (frame[:, :, 1] + glow * 28).astype(np.uint8)
    frame[:, :, 2] = (frame[:, :, 2] + glow * 48).astype(np.uint8)
    cv2.putText(
        frame,
        "hear-me",
        (24, height - 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (100, 116, 139),
        2,
        cv2.LINE_AA,
    )
    return frame


class _MockCapture:
    def __init__(self, *_args, **_kwargs):
        self._frame = _placeholder_bgr()

    def isOpened(self) -> bool:
        return True

    def read(self):
        return True, self._frame.copy()

    def release(self) -> None:
        pass


class _MockInference:
    def __init__(self, *_args, **_kwargs):
        self.config = {"window_size": 32}
        self.input_queue = deque([0] * 32, maxlen=32)
        self.pred = "привет"
        self.running = True

    def start(self) -> None:
        pass

    def stop(self) -> None:
        self.running = False


def _hwnd(widget) -> int:
    wid = widget.winfo_id()
    if sys.platform == "win32":
        import ctypes

        parent = ctypes.windll.user32.GetParent(wid)
        return parent if parent else wid
    return wid


def _bring_to_front(widget) -> None:
    widget.deiconify()
    widget.lift()
    widget.attributes("-topmost", True)
    widget.update_idletasks()
    widget.update()
    widget.focus_force()
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.SetForegroundWindow(_hwnd(widget))
    widget.attributes("-topmost", False)
    widget.update_idletasks()
    widget.update()
    time.sleep(0.15)


def _grab_win32(hwnd: int) -> Image.Image:
    import ctypes
    from ctypes import wintypes

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.c_uint32 * 3)]

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise OSError("GetWindowRect failed")

    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid window size: {width}x{height}")

    hwnd_dc = user32.GetWindowDC(hwnd)
    if not hwnd_dc:
        raise OSError("GetWindowDC failed")

    try:
        mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
        if not mem_dc:
            raise OSError("CreateCompatibleDC failed")

        try:
            bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
            if not bmp:
                raise OSError("CreateCompatibleBitmap failed")

            try:
                gdi32.SelectObject(mem_dc, bmp)
                ok = user32.PrintWindow(hwnd, mem_dc, 2)
                if not ok:
                    user32.PrintWindow(hwnd, mem_dc, 0)

                bmi = BITMAPINFO()
                bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                bmi.bmiHeader.biWidth = width
                bmi.bmiHeader.biHeight = -height
                bmi.bmiHeader.biPlanes = 1
                bmi.bmiHeader.biBitCount = 32
                bmi.bmiHeader.biCompression = 0

                buf = (ctypes.c_ubyte * (width * height * 4))()
                lines = gdi32.GetDIBits(
                    mem_dc, bmp, 0, height, buf, ctypes.byref(bmi), 0
                )
                if not lines:
                    raise OSError("GetDIBits failed")

                return Image.frombuffer("RGBA", (width, height), bytes(buf), "raw", "BGRA", 0, 1)
            finally:
                gdi32.DeleteObject(bmp)
        finally:
            gdi32.DeleteDC(mem_dc)
    finally:
        user32.ReleaseDC(hwnd, hwnd_dc)


def _grab(widget: ctk.CTk | ctk.CTkToplevel, path: Path, label: str) -> None:
    print(f"\n[{label}] Сверните лишние окна. Снимок через {COUNTDOWN_SEC} с…")
    for left in range(COUNTDOWN_SEC, 0, -1):
        print(f"  {left}…", flush=True)
        time.sleep(1)

    _bring_to_front(widget)
    widget.update_idletasks()
    widget.update()
    time.sleep(0.2)

    if sys.platform == "win32":
        img = _grab_win32(_hwnd(widget)).convert("RGB")
    else:
        from PIL import ImageGrab

        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        w = max(widget.winfo_width(), 1)
        h = max(widget.winfo_height(), 1)
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")
    print(f"  -> {path.relative_to(ROOT)}")


def _patch_runtime() -> None:
    import cv2 as cv2_mod

    cv2_mod.VideoCapture = _MockCapture  # type: ignore[misc, assignment]

    import utils as utils_mod

    utils_mod.SLInference = _MockInference  # type: ignore[misc, assignment]


def _stop_app(app) -> None:
    if hasattr(app, "_running"):
        app._running = False
    if hasattr(app, "inference"):
        app.inference.stop()
    if hasattr(app, "cap"):
        app.cap.release()
    if hasattr(app, "speech"):
        app.speech.stop()


def capture_demo_main() -> ctk.CTk:
    from demo import GestureDemoApp

    app = GestureDemoApp()
    app.history.extend(["спасибо", "привет"])
    app.gesture_label.configure(text="привет")
    app.buffer_bar.set(1.0)
    app.buffer_label.configure(text="32 / 32")
    app._refresh_history()
    rgb = cv2.cvtColor(_placeholder_bgr(), cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(640, 480))
    app.video_label.configure(image=ctk_img)
    app._photo_ref = ctk_img
    return app


def capture_pro_main(mode: str = "live") -> ctk.CTk:
    from pro import GestureProApp

    app = GestureProApp()
    rgb = cv2.cvtColor(_placeholder_bgr(), cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(640, 480))
    app.video_label.configure(image=ctk_img)
    app._photo_ref = ctk_img

    if mode == "phrase":
        app.work_mode.set("Запись фразы")
        app._on_work_mode_change("Запись фразы")
        app.recording = True
        app._update_record_ui()
        app.phrase_label.configure(
            text="Идёт запись… покажите жесты, затем R или «Остановить»",
            text_color="#EF4444",
        )
    else:
        app.gesture_label.configure(text="спасибо")
        app.history.append("спасибо")
        app._refresh_history()
        app.buffer_bar.set(1.0)
        app.buffer_label.configure(text="32 / 32")

    return app


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _patch_runtime()
    ctk.set_appearance_mode("dark")

    print("=== Захват скриншотов для README ===")
    print("Окна приложения появятся по очереди; перед каждым снимком — пауза 3 с.")

    from services.tutorial_dialog import TutorialCarouselDialog
    from services.upgrade_dialog import UpgradeProDialog

    demo = capture_demo_main()
    _grab(demo, OUT_DIR / "01-demo-main.png", "Demo — главное окно")

    tutorial = TutorialCarouselDialog(demo, edition="demo")
    tutorial.update()
    _grab(tutorial, OUT_DIR / "02-demo-tutorial.png", "Demo — туториал")
    tutorial.destroy()

    upgrade = UpgradeProDialog(demo)
    upgrade.update()
    _grab(upgrade, OUT_DIR / "03-upgrade-pro.png", "Demo — активация PRO")
    upgrade.destroy()

    _stop_app(demo)
    demo.destroy()

    pro = capture_pro_main("live")
    _grab(pro, OUT_DIR / "04-pro-live.png", "Pro — реальное время")

    tutorial_pro = TutorialCarouselDialog(pro, edition="pro")
    tutorial_pro.update()
    _grab(tutorial_pro, OUT_DIR / "05-pro-tutorial.png", "Pro — туториал")
    tutorial_pro.destroy()

    _stop_app(pro)
    pro.destroy()

    pro_phrase = capture_pro_main("phrase")
    _grab(pro_phrase, OUT_DIR / "06-pro-phrase-recording.png", "Pro — запись фразы")
    _stop_app(pro_phrase)
    pro_phrase.destroy()

    print(f"\nГотово: {len(list(OUT_DIR.glob('*.png')))} файлов в doc/screenshots/")


if __name__ == "__main__":
    main()
