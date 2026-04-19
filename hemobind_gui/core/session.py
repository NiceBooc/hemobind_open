import json
from pathlib import Path

class SessionManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.last_session_path = self.config_dir / "last_session.json"

    def save_session(self, path: Path, data: dict):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            # Also save as last session
            with open(self.last_session_path, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self, path: Path) -> dict:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def load_last_session(self) -> dict:
        if self.last_session_path.exists():
            return self.load_session(self.last_session_path)
        return None
