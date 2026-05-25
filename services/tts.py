import queue
import threading
from typing import Optional


class SpeechEngine:
    """Озвучка жестов. На Windows — новый движок на каждую фразу (pyttsx3 не зависает)."""

    def __init__(self, rate: int = 175, volume: float = 1.0):
        self._rate = rate
        self._volume = max(0.0, min(1.0, volume))
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _pick_russian_voice(self, engine) -> None:
        for voice in engine.getProperty("voices"):
            name = (voice.name or "").lower()
            vid = (voice.id or "").lower()
            if any(x in name or x in vid for x in ("ru", "russian", "irina", "pavel")):
                engine.setProperty("voice", voice.id)
                return

    def _speak_phrase(self, text: str) -> None:
        import pyttsx3

        engine = pyttsx3.init()
        try:
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            self._pick_russian_voice(engine)
            engine.say(text)
            engine.runAndWait()
        finally:
            try:
                engine.stop()
            except Exception:
                pass

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            if text.strip():
                self._speak_phrase(text.strip())

    def speak(self, text: str) -> None:
        self._queue.put(text)

    def update_settings(self, rate: int, volume: float) -> None:
        self._rate = rate
        self._volume = max(0.0, min(1.0, volume))

    def stop(self) -> None:
        self._queue.put(None)
