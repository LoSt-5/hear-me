import json
import time
from collections import deque
from pathlib import Path
from threading import Thread

from model import Predictor
from paths import app_root

ROOT = app_root()
DEFAULT_CONFIG = ROOT / "configs" / "config.json"


class SLInference:
    def __init__(self, config_path=None):
        config_path = Path(config_path or DEFAULT_CONFIG)
        self.running = True
        self.config = self.read_config(config_path)
        self.model = Predictor(self.config)
        self.input_queue = deque(maxlen=self.config["window_size"])
        self.pred = ""
        self.thread = None

    def read_config(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        root = config_path.parent.parent
        for key in ("path_to_model", "path_to_class_list"):
            path = Path(config[key])
            if not path.is_absolute():
                config[key] = str(root / path)
        return config

    def worker(self):
        while self.running:
            if len(self.input_queue) == self.config["window_size"]:
                pred_dict = self.model.predict(list(self.input_queue))
                if pred_dict:
                    self.pred = pred_dict["labels"][0]
                    self.input_queue.clear()
                else:
                    self.pred = ""
            time.sleep(0.1)

    def start(self):
        self.thread = Thread(target=self.worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
